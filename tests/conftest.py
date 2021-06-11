import os
import os.path
import subprocess

import pytest
import sys


LAYOUTS = {
    "single-package": {
        "foo/__init__.py": os.path.join("foo", "__init__.py"),
    },
    "single-module": {
        "foo.py": "foo.py",
    },
    "single-package-multiple-modules": {
        "foo/__init__.py": os.path.join("foo", "__init__.py"),
        "foo/bar.py": os.path.join("foo", "bar.py"),
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
        "bar/__init__.py": os.path.join("src", "bar", "__init__.py"),
        "bar/baz/__init__.py": os.path.join("src", "bar", "baz", "__init__.py"),
    },
    "mixed-indirect-module-and-package": {
        "foo.py": os.path.join("src", "foo.py"),
        "bar/__init__.py": os.path.join("bar", "__init__.py"),
    },
    "namespace-package-only": {
        "foo/bar/__init__.py": os.path.join("foo", "bar", "__init__.py"),
    },
}


@pytest.fixture(params=LAYOUTS.values(), ids=LAYOUTS.keys())
def dummy_paths(request, tmp_path):
    input_directory = tmp_path / "in"
    input_directory.mkdir()

    paths = {t: os.path.join(input_directory, s) for t, s in request.param.items()}
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


@pytest.fixture
def path_runner(tmp_path):
    def module_path_to_spec(path):
        return path.replace("/__init__.py", "").replace(".py", "").rstrip("/").replace("/", ".")

    def run(*module_paths, python_path):
        runner_directory = tmp_path / "runner"
        runner_directory.mkdir()
        runner = runner_directory / "runner.py"
        runner.write_text(
            f'import site\nsite.addsitedir(r"{python_path}")\n'
            + "".join(f"import {module_path_to_spec(p)}\n" for p in module_paths),
            encoding="utf-8",
        )
        subprocess.check_call([sys.executable, str(runner)])

    yield run
