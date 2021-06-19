import argparse
from collections.abc import Iterator, Sequence
import json
import os
import os.path
import posixpath
import subprocess
import sys
import tempfile
import zipfile

from . import BaseEditableInstaller, EditableDistributionMetadata, EditableStrategy, install


def _slice_pairs(path_map: "Sequence[str]") -> "list[tuple[str, str]]":
    if len(path_map) % 2:
        raise ValueError("Sequence must be even in length", path_map)

    it = iter(path_map)
    return list(zip(it, it))


def _get_sources(path: str) -> "Iterator[str]":
    try:
        for entry in os.scandir(path):
            if entry.name == "__pycache__":
                continue
            elif entry.is_file():
                yield entry.path
            elif entry.is_dir():
                yield from _get_sources(entry.path)
    except NotADirectoryError:
        yield path


def _replace_prefix_and_posixify(entry: str, map_from: str, map_to: str) -> str:
    if not os.path.commonpath([entry, map_from]) == map_from:
        raise ValueError("Unmapped prefix", (entry, map_from))

    return os.path.join(map_to, os.path.relpath(entry, map_from)).replace(
        os.path.sep, posixpath.sep
    )


def _get_paths(map_from: str, map_to: str) -> "Iterator[tuple[str, str]]":
    contents = _get_sources(map_from)
    return (
        (_replace_prefix_and_posixify(e, map_from, map_to), os.path.abspath(e)) for e in contents
    )


def _rebuild_wheel(tempdir: str, wheel_path: str) -> None:
    with zipfile.ZipFile(wheel_path) as wheel:
        wheel.extractall(
            tempdir,
            (
                n
                for n in wheel.namelist()
                for h, _, _ in (n.partition(posixpath.sep),)
                if h.endswith((".data", ".dist-info"))
            ),
        )

    with zipfile.ZipFile(wheel_path, "w") as wheel:
        for file in _get_sources(tempdir):
            absolute_path = os.path.join(tempdir, file)
            in_wheel_path = os.path.relpath(file, tempdir)
            if os.path.basename(file) == "RECORD":
                with open(absolute_path, encoding="utf-8") as record_file:
                    record_entries = record_file.read().splitlines()
                wheel.writestr(
                    in_wheel_path,
                    "".join(
                        e + "\n"
                        for e in record_entries
                        for p, _, _ in (e.partition(","),)
                        for h, _, _ in (p.partition(posixpath.sep),)
                        if h.endswith((".data", ".dist-info"))
                    ),
                )
            elif absolute_path == wheel_path:
                continue
            else:
                wheel.write(absolute_path, in_wheel_path)


def _pip_build_wheel(tempdir: str, spec: str) -> str:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "wheel", "--no-deps", "--wheel-dir", tempdir, spec],
    )
    return next(os.scandir(tempdir)).path


def _pip_install_wheel(wheel_path: str, spec: str) -> None:
    extras_sep = spec.find("[")
    extras = spec[extras_sep:] if extras_sep != -1 else ""
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", wheel_path + extras],
    )


def _pip_info_json() -> "list[dict[str, str]]":
    return json.loads(
        subprocess.check_output(
            [sys.executable, "-m", "pip", "--verbose", "list", "--format", "json"],
        )
    )


def main(args: "Sequence[str] | None" = None) -> None:
    parser = argparse.ArgumentParser(
        description="Wacky transitional editable project installer.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        prog=f"{os.path.basename(sys.executable)} -m frontend_editables.transitional_cli",
    )
    parser.add_argument(
        "path_pairs",
        nargs="+",
        help="pairs of path on disk and corresponding path in the virtual wheel (posix)",
    )
    parser.add_argument(
        "--method",
        choices=[i.label for i in BaseEditableInstaller.registry],
        help="editable installation method to use",
    )
    parser.add_argument(
        "--strategy",
        choices=[s.value for s in EditableStrategy],
        default=EditableStrategy.lax.value,
        help="editable strategy to follow",
        type=EditableStrategy,
    )
    parser.add_argument(
        "--spec",
        default=".",
        help="requirement specifier",
    )
    parsed_args = parser.parse_args(args)

    path_pairs = _slice_pairs(parsed_args.path_pairs)
    paths = dict(
        p
        for f, t in path_pairs
        for p in _get_paths(os.path.relpath(os.path.normpath(f), os.getcwd()), os.path.normpath(t))
    )
    editable_metadata: EditableDistributionMetadata = {"paths": paths}

    if parsed_args.method is not None:
        installer_cls = next(
            i for i in BaseEditableInstaller.registry if i.label == parsed_args.method
        )
    else:
        installer_cls = None

    with tempfile.TemporaryDirectory(prefix="frontend-editables-transitional-cli") as tempdir:
        wheel_path = _pip_build_wheel(tempdir, parsed_args.spec)
        _rebuild_wheel(tempdir, wheel_path)
        _pip_install_wheel(wheel_path, parsed_args.spec)
        pip_info = _pip_info_json()
        distribution, _, _ = os.path.basename(wheel_path).partition("-")
        normalized_distribution = distribution.replace("_", "-")
        package = next(i for i in pip_info if i["name"] == normalized_distribution)
        install(
            package["name"],
            package["location"],
            editable_metadata,
            parsed_args.strategy,
            installer_cls,
            append_to_record=os.path.join(
                package["location"], f"{distribution}-{package['version']}.dist-info", "RECORD"
            ),
        )


if __name__ == "__main__":
    main()
