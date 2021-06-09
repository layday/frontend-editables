import os
import os.path

import pytest


LAYOUTS = {
    "single-package": {
        "foo/__init__.py": os.path.join("foo", "__init__.py"),
    },
    "single-module": {
        "foo.py": "foo.py",
    },
    "mixed-module-and-package": {
        "foo.py": "foo.py",
        "bar/__init__.py": os.path.join("bar", "__init__.py"),
    },
    "multiple-package": {
        "foo/__init__.py": os.path.join("foo", "__init__.py"),
        "bar/__init__.py": os.path.join("bar", "__init__.py"),
    },
    "multiple-indirect-package": {
        "foo/__init__.py": os.path.join("foo", "__init__.py"),
        "bar/__init__.py": os.path.join("lib", "baz", "__init__.py"),
    },
    "multiple-nested-package": {
        "foo/__init__.py": os.path.join("src", "foo", "__init__.py"),
        "bar/baz/__init__.py": os.path.join("src", "bar", "baz", "__init__.py"),
    },
    "mixed-module-and-package": {
        "foo.py": os.path.join("src", "foo.py"),
        "bar/__init__.py": os.path.join("bar", "__init__.py"),
    },
}


@pytest.fixture(params=LAYOUTS.values(), ids=LAYOUTS.keys())
def dummy_paths(request, tmp_path):
    input_ = tmp_path / "input"
    input_.mkdir()
    paths = {t: os.path.join(input_, s) for t, s in request.param.items()}
    for source in paths.values():
        os.makedirs(os.path.dirname(source), exist_ok=True)
        with open(source, "wb"):
            pass

    yield {"paths": paths}


@pytest.fixture
def dummy_dist_info(tmp_path):
    dist_info = tmp_path.joinpath("foo-0.0.0.dist-info")
    dist_info.mkdir()
    dist_info.joinpath("METADATA").write_text(
        "Name: foo\n",
        encoding="utf-8",
    )
    dist_info.joinpath("RECORD").write_text(
        "foo-0.0.0.dist-info/METADATA,,\nfoo-0.0.0.dist-info/RECORD,,\n",
        encoding="utf-8",
    )
    yield dist_info
