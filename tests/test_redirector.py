import contextlib

import pytest

import frontend_editables


@contextlib.contextmanager
def nullcontext():
    yield


@pytest.fixture
def errorcontext(request):
    if request.node.callspec.id == "namespace-package-only":
        yield pytest.raises(
            frontend_editables.InstallerOperationError,
            match="Implicit namespace packages are not supported",
        )
    else:
        yield nullcontext()


def test_redirector_paths_are_added_to_record(
    tmp_path, dummy_paths, dummy_dist_info, errorcontext
):
    output_directory = tmp_path / "out"
    output_directory.mkdir()

    with errorcontext:
        frontend_editables.install(
            output_directory,
            dummy_paths,
            frontend_editables.EditableStrategy.lax,
            frontend_editables.RedirectorInstaller,
            append_to_record=dummy_dist_info / "RECORD",
        )
        (pth_file,) = output_directory.glob("*.pth")
        assert (
            (dummy_dist_info / "RECORD")
            .read_text(encoding="utf-8")
            .endswith(f"{pth_file.name},,\n")
        )


def test_redirector_modules_can_be_imported(tmp_path, dummy_paths, path_runner, errorcontext):
    output_directory = tmp_path / "out"
    output_directory.mkdir()

    with errorcontext:
        frontend_editables.install(
            output_directory,
            dummy_paths,
            frontend_editables.EditableStrategy.lax,
            frontend_editables.RedirectorInstaller,
        )
        path_runner(*dummy_paths["paths"], python_path=output_directory)
