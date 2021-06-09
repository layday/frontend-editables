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
def errorcontext(request, dummy_paths):
    if request.node.callspec.id == "multiple-indirect-package":
        yield pytest.raises(
            frontend_editables.InstallerOperationError,
            match="The target is not a subpath of its source.",
        )
    else:
        yield nullcontext()


def test_package_paths_are_added_to_pth_file(tmp_path, dummy_paths, errorcontext):
    output_directory = tmp_path / "out"
    output_directory.mkdir()

    with errorcontext:
        frontend_editables.install(
            output_directory,
            dummy_paths,
            frontend_editables.EditableStrategy.lax,
            frontend_editables.PthFileInstaller,
        )
        (pth_file,) = output_directory.glob("*.pth")
        assert pth_file.read_text(encoding="utf-8") == "\n".join(
            uniq(
                os.path.dirname(os.path.dirname(s)) if posixpath.sep in t else os.path.dirname(s)
                for t, s in dummy_paths["paths"].items()
                if t.count(posixpath.sep) <= 1
            )
        )


def test_pth_file_path_is_added_to_record(tmp_path, dummy_paths, dummy_dist_info, errorcontext):
    output_directory = tmp_path / "out"
    output_directory.mkdir()

    with errorcontext:
        frontend_editables.install(
            output_directory,
            dummy_paths,
            frontend_editables.EditableStrategy.lax,
            frontend_editables.PthFileInstaller,
            append_to_record=dummy_dist_info / "RECORD",
        )
        (pth_file,) = output_directory.glob("*.pth")
        assert (
            (dummy_dist_info / "RECORD")
            .read_text(encoding="utf-8")
            .endswith(f"{pth_file.name},,\n")
        )
