from collections.abc import Collection
from functools import lru_cache
import importlib.machinery
from itertools import starmap
import os
import os.path
from pathlib import Path
import pkgutil
import posixpath
import tempfile
from typing import TYPE_CHECKING

from ._utils import GenericGetitem, uniq

if TYPE_CHECKING:
    from typing_extensions import Protocol, TypeAlias, TypedDict
else:
    Protocol = TypeAlias = TypedDict = GenericGetitem

_PathOrStr: TypeAlias = "os.PathLike[str] | str"


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


def _normalize_module_name(name: str, suffixes: "tuple[str, ...]") -> str:
    if "." not in name:
        return name
    (suffix,) = (s for s in suffixes if name.endswith(s))
    name = name[: name.rfind(suffix)]
    return name


def _normalize_package_path(source: str) -> str:
    if os.path.isdir(source):
        source = os.path.join(source, "__init__.py")
        if not os.path.isfile(source):
            raise InstallerOperationError(
                "Implicit namespace packages are not supported by the redirector installer.",
                source,
            )
    return source


@lru_cache()
def _can_symlink(output_directory: _PathOrStr) -> bool:
    with tempfile.TemporaryDirectory(
        prefix="_test-frontend-editables-symlinking", dir=output_directory
    ) as tempdir:
        try:
            Path(tempdir, "bar").symlink_to(Path(tempdir, "foo"))
            return True
        except (AttributeError, NotImplementedError, OSError):
            return False


def _append_to_record(
    output_directory: _PathOrStr, record_path: _PathOrStr, installed_files: "Collection[Path]"
) -> None:
    with open(record_path, "a", encoding="utf-8") as record:
        record.writelines(
            f"{posixpath.sep.join(f.relative_to(output_directory).parts)},,\n"
            for f in installed_files
        )


class Installer(Protocol):  # pragma: no cover
    def __init__(
        self,
        name: str,
        output_directory: _PathOrStr,
        editable_metadata: EditableDistributionMetadata,
    ) -> None:
        ...

    def is_installation_method_supported(self) -> bool:
        ...

    def install(self) -> "list[Path]":
        ...


class _BaseInstaller:
    def __init__(
        self,
        name: str,
        output_directory: _PathOrStr,
        editable_metadata: EditableDistributionMetadata,
    ) -> None:
        self.name = name
        self.output_directory = Path(output_directory)
        self.editable_metadata = editable_metadata

    def is_installation_method_supported(self) -> bool:
        return True


class _SymlinkInstaller(_BaseInstaller):
    def is_installation_method_supported(self) -> bool:
        return _can_symlink(self.output_directory)


class StrictSymlinkInstaller(_SymlinkInstaller):
    def install(self) -> "list[Path]":
        paths = self.editable_metadata["paths"]
        packages = uniq(
            self.output_directory / d for t in paths for d in (posixpath.dirname(t),) if d
        )
        for package_path in packages:
            os.makedirs(package_path, exist_ok=True)

        all_files = [self.output_directory / t for t in paths]
        for target_path, source in zip(all_files, paths.values()):
            target_path.symlink_to(source)

        return all_files


class LaxSymlinkInstaller(_SymlinkInstaller):
    def install(self) -> "list[Path]":
        paths = self.editable_metadata["paths"]
        outermost_entities = uniq(starmap(_find_outermost_entity, paths.items()))
        outermost_paths = [self.output_directory / t for t, _ in outermost_entities]
        for target_path, (_, source) in zip(outermost_paths, outermost_entities):
            target_path.symlink_to(source)

        return outermost_paths


class RedirectorInstaller(_BaseInstaller):
    _redirector = pkgutil.get_data(__package__, "_redirector.py")
    _module_suffixes = tuple(importlib.machinery.all_suffixes())

    def install(self) -> "list[Path]":
        paths = self.editable_metadata["paths"]
        outermost_entities = uniq(starmap(_find_outermost_entity, paths.items()))
        specs_to_absolute_paths = {
            # Shear off the extension from module filenames.
            _normalize_module_name(t, self._module_suffixes):
            # Append ``/__init__.py`` to the path if it's a package.
            _normalize_package_path(s)
            for t, s in outermost_entities
        }
        base_name = f"_editable_{self.name}"
        editables_path = self.output_directory / f"{base_name}.py"
        assert self._redirector
        editables_path.write_bytes(self._redirector)
        pth_file_path = self.output_directory / f"{base_name}.pth"
        pth_file_path.write_text(
            # fmt: off
            f"import {base_name}; "
            f"{base_name}.install_redirector({specs_to_absolute_paths})",
            # fmt: on
            encoding="utf-8",
        )
        return [editables_path, pth_file_path]


class PthFileInstaller(_BaseInstaller):
    def install(self) -> "list[Path]":
        paths = self.editable_metadata["paths"]
        parent_folders = uniq(starmap(_find_parent_folder, paths.items()))
        pth_file_path = self.output_directory / f"_editable_{self.name}.pth"
        pth_file_path.write_text(
            "\n".join(parent_folders),
            encoding="utf-8",
        )
        return [pth_file_path]


def install(
    installer_classes: "Collection[type[Installer]]",
    name: str,
    output_directory: _PathOrStr,
    editable_metadata: EditableDistributionMetadata,
    *,
    append_to_record: "_PathOrStr | None" = None,
) -> "list[Path]":
    """Perform an editable installation and return the list of installed files."""
    installer = next(
        c
        for i in installer_classes
        for c in (i(name, output_directory, editable_metadata),)
        if c.is_installation_method_supported()
    )
    installed_files = installer.install()
    if append_to_record is not None:
        _append_to_record(output_directory, append_to_record, installed_files)
    return installed_files
