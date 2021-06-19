import posixpath

import pytest

import frontend_editables
from frontend_editables._utils import uniq


def test_symlink_lax_strategy_outermost_entities_are_symlinked_successfully(tmp_path, dummy_paths):
    output_directory = tmp_path / "out"
    output_directory.mkdir()

    frontend_editables.install(
        "test_symlink",
        output_directory,
        dummy_paths,
        frontend_editables.EditableStrategy.lax,
    )
    assert all(
        e.is_symlink() and e.exists() if e.parent == output_directory else not e.is_symlink()
        for t in dummy_paths["paths"]
        for e in (output_directory / t,)
    )


def test_symlink_strict_strategy_files_are_symlinked_successfully(tmp_path, dummy_paths):
    output_directory = tmp_path / "out"
    output_directory.mkdir()

    frontend_editables.install(
        "test_symlink",
        output_directory,
        dummy_paths,
        frontend_editables.EditableStrategy.strict,
        frontend_editables.SymlinkInstaller,
    )
    assert all(
        f.is_symlink() and f.is_file() and not f.parent.is_symlink()
        for t in dummy_paths["paths"]
        if not t.endswith(posixpath.sep)
        for f in (output_directory / t,)
    )


def test_symlink_lax_strategy_outermost_entities_are_added_to_record(
    tmp_path, dummy_dist_info, dummy_paths
):
    output_directory = tmp_path / "out"
    output_directory.mkdir()

    frontend_editables.install(
        "test_symlink",
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


def test_symlink_strict_strategy_files_are_added_to_record(tmp_path, dummy_dist_info, dummy_paths):
    output_directory = tmp_path / "out"
    output_directory.mkdir()

    frontend_editables.install(
        "test_symlink",
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


@pytest.mark.parametrize("strategy", frontend_editables.EditableStrategy)
def test_symlinks_can_be_imported(tmp_path, dummy_paths, path_runner, strategy):
    output_directory = tmp_path / "out"
    output_directory.mkdir()

    frontend_editables.install(
        "test_symlink",
        output_directory,
        dummy_paths,
        strategy,
        frontend_editables.SymlinkInstaller,
    )
    path_runner(*dummy_paths["paths"], python_path=output_directory)
