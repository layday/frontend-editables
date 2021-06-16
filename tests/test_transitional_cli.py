import json
import os
import os.path
import shutil
import subprocess
import sysconfig
import venv

import pytest


@pytest.fixture(autouse=True, scope="module")
def transitional_cli_dependencies(tmp_path_factory):
    dependency_directory = tmp_path_factory.getbasetemp() / "_transitional-cli-dependencies"
    shutil.copytree(
        sysconfig.get_paths()["purelib"],
        dependency_directory,
        ignore=shutil.ignore_patterns("*.dist-info", "*.pth"),
    )
    yield dependency_directory


@pytest.fixture
def test_env(tmp_path, monkeypatch, transitional_cli_dependencies):
    test_env_directory = tmp_path / "test-env"
    venv.create(test_env_directory)
    paths = sysconfig.get_paths(vars={"base": test_env_directory})
    coverage_pth_file = os.path.join(sysconfig.get_paths()["purelib"], "00-coverage.pth")
    if os.path.isfile(coverage_pth_file):
        shutil.copy(coverage_pth_file, paths["purelib"])
    monkeypatch.setenv("PYTHONPATH", str(transitional_cli_dependencies))
    yield paths


@pytest.fixture
def test_env_executable(test_env):
    exe = os.path.join(test_env["scripts"], "python.exe" if os.name == "nt" else "python")
    yield exe


def test_self_install_from_path_with_default_settings(test_env_executable):
    subprocess.check_call(
        [
            test_env_executable,
            "-m",
            "frontend_editables.transitional_cli",
            "src/frontend_editables",
            "frontend_editables",
        ]
    )
    pip_list = json.loads(
        subprocess.check_output([test_env_executable, "-m", "pip", "list", "--format", "json"])
    )
    assert any(p["name"] == "frontend-editables" for p in pip_list)


def test_self_install_from_path_with_spec(test_env_executable):
    subprocess.check_call(
        [
            test_env_executable,
            "-m",
            "frontend_editables.transitional_cli",
            "--spec",
            ".[test]",
            "src/frontend_editables",
            "frontend_editables",
        ]
    )
    pip_list = json.loads(
        subprocess.check_output([test_env_executable, "-m", "pip", "list", "--format", "json"])
    )
    assert sum(p["name"] in {"frontend-editables", "pytest"} for p in pip_list) == 2
