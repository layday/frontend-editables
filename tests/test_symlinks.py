import posixpath

import pytest

import frontend_editables
from frontend_editables._utils import uniq


def test_lax_strategy_only_outermost_entities_are_symlinked(tmp_path, dummy_paths):
    output_directory = tmp_path / "out"
    output_directory.mkdir()

    frontend_editables.install(
        output_directory,
        dummy_paths,
        frontend_editables.EditableStrategy.lax,
    )
    assert all(
        (c == 0 and e.is_symlink())
        or (c == 1 and not e.is_symlink() and e.parent.is_symlink())
        or (c >= 2 and not e.is_symlink() and not e.parent.is_symlink())
        for t in dummy_paths["paths"]
        for e, c in ((output_directory / t, t.count(posixpath.sep)),)
    )


def test_strict_strategy_only_files_are_symlinked(tmp_path, dummy_paths):
    output_directory = tmp_path / "out"
    output_directory.mkdir()

    frontend_editables.install(
        output_directory,
        dummy_paths,
        frontend_editables.EditableStrategy.strict,
        frontend_editables.SymlinkInstaller,
    )
    assert all(
        f.is_symlink() and not f.parent.is_symlink()
        for t in dummy_paths["paths"]
        for f in (output_directory / t,)
    )


def test_lax_strategy_outermost_entities_are_added_to_record(tmp_path, dummy_dist_info, dummy_paths):
    output_directory = tmp_path / "out"
    output_directory.mkdir()

    frontend_editables.install(
        output_directory,
        dummy_paths,
        frontend_editables.EditableStrategy.lax,
        frontend_editables.SymlinkInstaller,
        append_to_record=dummy_dist_info / "RECORD",
    )
    assert (
        (dummy_dist_info / "RECORD")
        .read_text(encoding="utf-8")
        .endswith(
            "".join(
                f"{d},,\n"
                for d in uniq(t.partition(posixpath.sep)[0] for t in dummy_paths["paths"])
            )
        )
    )


def test_strict_strategy_paths_are_added_to_record(tmp_path, dummy_dist_info, dummy_paths):
    output_directory = tmp_path / "out"
    output_directory.mkdir()

    frontend_editables.install(
        output_directory,
        dummy_paths,
        frontend_editables.EditableStrategy.strict,
        frontend_editables.SymlinkInstaller,
        append_to_record=dummy_dist_info / "RECORD",
    )
    assert (
        (dummy_dist_info / "RECORD")
        .read_text(encoding="utf-8")
        .endswith("".join(f"{t},,\n" for t in dummy_paths["paths"]))
    )
