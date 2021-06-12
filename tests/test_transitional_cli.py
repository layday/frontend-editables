import json
import os
import os.path
import subprocess
import sys
import sysconfig
import venv

import pytest


@pytest.fixture
def test_env(tmp_path):
    test_env_directory = tmp_path / "test-env"
    test_env = venv.EnvBuilder(with_pip=True)
    test_env.create(test_env_directory)
    test_env_paths = sysconfig.get_paths(vars={"base": test_env_directory})
    yield test_env_paths


def test_self_install_from_path_with_default_settings(test_env):
    python_executable = os.path.join(test_env["scripts"], os.path.basename(sys.executable))

    install_args = [python_executable, "-m", "pip", "install", "typing-extensions"]
    if sys.version_info < (3, 7):
        # Old pip does not support PEP 517.
        install_args += ["-U", "pip"]

    subprocess.check_call(install_args)
    subprocess.check_call(
        [
            python_executable,
            "-m",
            "frontend_editables.transitional_cli",
            "src/frontend_editables",
            "frontend_editables",
        ],
        env={**os.environ, "PYTHONPATH": "src"},
    )
    pip_list = json.loads(
        subprocess.check_output([python_executable, "-m", "pip", "list", "--format", "json"])
    )
    assert any(p["name"] == "frontend-editables" for p in pip_list)


def test_self_install_from_path_with_spec(test_env):
    python_executable = os.path.join(test_env["scripts"], os.path.basename(sys.executable))

    install_args = [python_executable, "-m", "pip", "install", "typing-extensions"]
    if sys.version_info < (3, 7):
        # Old pip does not support PEP 517.
        install_args += ["-U", "pip"]

    subprocess.check_call(install_args)
    subprocess.check_call(
        [
            python_executable,
            "-m",
            "frontend_editables.transitional_cli",
            "--spec",
            ".[test]",
            "src/frontend_editables",
            "frontend_editables",
        ],
        env={**os.environ, "PYTHONPATH": "src"},
    )
    pip_list = json.loads(
        subprocess.check_output([python_executable, "-m", "pip", "list", "--format", "json"])
    )
    assert sum(p["name"] in {"frontend-editables", "pytest"} for p in pip_list) == 2
