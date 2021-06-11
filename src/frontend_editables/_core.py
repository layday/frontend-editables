from collections.abc import Collection, Set
import enum
from functools import lru_cache
from itertools import starmap
import os
import os.path
from pathlib import Path
import pkgutil
import posixpath
import tempfile

from typing_extensions import Final, TypeAlias, TypedDict

from ._utils import shasum, uniq

_PathOrStr: TypeAlias = "os.PathLike[str] | str"


class EditableStrategy(str, enum.Enum):
    lax = "lax"
    strict = "strict"


class InstallerOperationError(RuntimeError):
    pass


class EditableDistributionMetadata(TypedDict):
    paths: "dict[str, str]"


def _find_outermost_entity(target: str, source: str) -> "tuple[str, str]":
    target = os.path.normpath(target)
    while os.path.sep in target:
        target = os.path.dirname(target)
        source = os.path.dirname(source)
    return (target, source)


def _find_parent_folder(target: str, source: str) -> str:
    target, source = _find_outermost_entity(target, source)
    if not source.endswith(target):
        raise InstallerOperationError(
            "The target is not a subpath of its source.  For packages to be added "
            "on the path using a ``.pth`` file, the package names in "
            "the source tree and the built distribution must match.",
            (target, source),
        )
    return os.path.dirname(source)


def _normalise_package_path(source: str) -> str:
    if os.path.isdir(source):
        source = os.path.join(source, "__init__.py")
        if not os.path.isfile(source):
            raise InstallerOperationError(
                "Implicit namespace packages are not supported by the redirector installer.",
                source,
            )
    return source


class BaseEditableInstaller:
    registry: Final["list[type[BaseEditableInstaller]]"] = []
    supported_strategies: "Set[EditableStrategy]"

    def __init__(
        self,
        output_directory: _PathOrStr,
        editable_metadata: EditableDistributionMetadata,
        strategy: EditableStrategy,
    ) -> None:
        self.output_directory: Path = Path(output_directory)
        self.editable_metadata: EditableDistributionMetadata = editable_metadata
        self.strategy = strategy

    def __init_subclass__(
        cls, supported_strategies: "Set[EditableStrategy]", priority: int
    ) -> None:
        cls.registry.insert(priority, cls)
        cls.supported_strategies = supported_strategies

    @property
    def strategy(self) -> EditableStrategy:
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: EditableStrategy) -> None:
        if strategy not in self.supported_strategies:
            raise ValueError("Unsupported strategy", strategy)
        self._strategy = strategy

    @classmethod
    def is_installation_method_supported(
        cls, output_directory: _PathOrStr
    ) -> bool:  # pragma: no cover
        raise NotImplementedError

    def install(self) -> "list[Path]":  # pragma: no cover
        raise NotImplementedError

    def append_to_record(
        self, record_path: _PathOrStr, installed_files: "Collection[Path]"
    ) -> None:
        with open(record_path, "a", encoding="utf-8") as record:
            record.writelines(
                f"{posixpath.sep.join(f.relative_to(self.output_directory).parts)},,\n"
                for f in installed_files
            )


class SymlinkInstaller(
    BaseEditableInstaller,
    supported_strategies=frozenset({EditableStrategy.lax, EditableStrategy.strict}),
    priority=0,
):
    @classmethod
    @lru_cache()
    def is_installation_method_supported(cls, output_directory: _PathOrStr) -> bool:
        with tempfile.TemporaryDirectory(
            prefix="_test-frontend-editables-symlinking",
            dir=output_directory,
        ) as tempdir:
            try:
                os.symlink(os.path.join(tempdir, "foo"), os.path.join(tempdir, "bar"))
                return True
            except (AttributeError, NotImplementedError, OSError):
                return False

    def install(self) -> "list[Path]":
        # Reassigning strategy for exhaustiveness check in Pyright.
        strategy: EditableStrategy = self.strategy
        paths = self.editable_metadata["paths"]

        if strategy is EditableStrategy.lax:
            outermost_entities = uniq(starmap(_find_outermost_entity, paths.items()))
            outermost_paths = [self.output_directory / t for t, _ in outermost_entities]
            for target_path, (_, source) in zip(outermost_paths, outermost_entities):
                os.symlink(source, target_path)

            return outermost_paths

        elif strategy is EditableStrategy.strict:
            packages = uniq(
                self.output_directory / d
                for t in paths
                for d in (posixpath.dirname(t),)
                if d
            )
            for package_path in packages:
                os.makedirs(package_path, exist_ok=True)

            all_files = [self.output_directory / t for t, _ in paths.items()]
            for target_path, source in zip(all_files, paths.values()):
                os.symlink(source, target_path)

            return all_files


class RedirectorInstaller(
    BaseEditableInstaller,
    supported_strategies=frozenset({EditableStrategy.lax}),
    priority=10,
):
    redirector = pkgutil.get_data(__package__, "_redirector.py")

    @classmethod
    def is_installation_method_supported(cls, output_directory: _PathOrStr) -> bool:
        return cls.redirector is not None

    def install(self) -> "list[Path]":
        paths = self.editable_metadata["paths"]
        outermost_entities = starmap(_find_outermost_entity, paths.items())
        specs_to_absolute_paths = {
            # Shear off the extension from module filenames.
            t[:-c] if c != -1 else t:
            # Append ``/__init__.py`` to the path if it's a package.
            _normalise_package_path(s)
            for t, s in outermost_entities
            for c in (t.find("."),)
        }
        base_name = f"_editable_{shasum(*outermost_entities)}"
        editables_path = self.output_directory / f"{base_name}.py"
        assert self.redirector
        editables_path.write_bytes(self.redirector)
        pth_file_path = self.output_directory / f"{base_name}.pth"
        pth_file_path.write_text(
            f"import {base_name}; " f"{base_name}.install_redirector({specs_to_absolute_paths})",
            encoding="utf-8",
        )
        return [editables_path, pth_file_path]


class PthFileInstaller(
    BaseEditableInstaller,
    supported_strategies=frozenset({EditableStrategy.lax}),
    priority=20,
):
    @classmethod
    def is_installation_method_supported(cls, output_directory: "os.PathLike[str] | str") -> bool:
        return True

    def install(self) -> "list[Path]":
        paths = self.editable_metadata["paths"]
        parent_folders = uniq(starmap(_find_parent_folder, paths.items()))
        pth_file_path = self.output_directory / f"_editable_{shasum(*parent_folders)}.pth"
        pth_file_path.write_text(
            "\n".join(parent_folders),
            encoding="utf-8",
        )
        return [pth_file_path]


def install(
    output_directory: _PathOrStr,
    editable_metadata: EditableDistributionMetadata,
    strategy: EditableStrategy,
    installer_cls: "type[BaseEditableInstaller] | None" = None,
    *,
    append_to_record: "os.PathLike[str] | str | None" = None,
) -> "list[Path]":
    """Perform an editable installation and return the list of installed files."""
    candidates = (
        c
        for c in ([installer_cls] if installer_cls is not None else BaseEditableInstaller.registry)
        if strategy in c.supported_strategies
        and c.is_installation_method_supported(output_directory)
    )
    installer_cls = next(candidates, None)
    if installer_cls is None:
        raise ValueError("No installer could satisfy strategy", strategy)

    installer = installer_cls(output_directory, editable_metadata, strategy)
    installed_files = installer.install()
    if append_to_record is not None:
        installer.append_to_record(append_to_record, installed_files)
    return installed_files
