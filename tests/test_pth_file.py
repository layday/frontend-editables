import contextlib
import os.path
import posixpath

import pytest

import frontend_editables
from frontend_editables._utils import uniq


@contextlib.contextmanager
def nullcontext():
    yield


@pytest.fixture
def errorcontext(request):
    if request.node.callspec.id == "multiple-indirect-package":
        yield pytest.raises(
            frontend_editables.InstallerOperationError,
            match="The target is not a subpath of its source",
        )
    else:
        yield nullcontext()


def test_parent_folders_are_listed_in_pth_file(tmp_path, dummy_paths, errorcontext):
    output_directory = tmp_path / "out"
    output_directory.mkdir()

    with errorcontext:
        frontend_editables.install(
            [frontend_editables.PthFileInstaller],
            "test_pth_file",
            output_directory,
            dummy_paths,
        )
        (pth_file,) = output_directory.glob("*.pth")
        assert pth_file.read_text(encoding="utf-8") == "\n".join(
            uniq(
                os.path.abspath(
                    os.path.join(
                        s,
                        *(
                            [os.path.pardir]
                            * ((not t.endswith(posixpath.sep)) + t.count(posixpath.sep))
                        ),
                    )
                )
                for t, s in dummy_paths["paths"].items()
            )
        )


def test_pth_file_is_added_to_record(tmp_path, dummy_paths, dummy_dist_info, errorcontext):
    output_directory = tmp_path / "out"
    output_directory.mkdir()

    with errorcontext:
        frontend_editables.install(
            [frontend_editables.PthFileInstaller],
            "test_pth_file",
            output_directory,
            dummy_paths,
            append_to_record=dummy_dist_info / "RECORD",
        )
        (pth_file,) = output_directory.glob("*.pth")
        assert (
            (dummy_dist_info / "RECORD")
            .read_text(encoding="utf-8")
            .endswith(f"{pth_file.name},,\n")
        )


def test_pth_file_submodules_can_be_imported(tmp_path, dummy_paths, path_runner, errorcontext):
    output_directory = tmp_path / "out"
    output_directory.mkdir()

    with errorcontext:
        frontend_editables.install(
            [frontend_editables.PthFileInstaller],
            "test_pth_file",
            output_directory,
            dummy_paths,
        )
        path_runner(*dummy_paths["paths"], python_path=output_directory)
