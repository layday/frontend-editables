import os.path
import subprocess
import sysconfig
import venv


def test_self_install_from_path_with_default_settings(tmp_path):
    venv_directory = tmp_path / "test-venv"
    test_env = venv.EnvBuilder(with_pip=True)
    test_env.create(venv_directory)
    paths = sysconfig.get_paths(vars={"base": venv_directory})
    python_executable = os.path.join(paths["scripts"], "python")
    subprocess.check_call([python_executable, "-m", "pip", "install", "typing-extensions"])
    subprocess.check_call(
        [
            python_executable,
            "-m",
            "frontend_editables.transitional_cli",
            "src/frontend_editables",
            "frontend_editables",
        ],
        env={"PYTHONPATH": "src"},
    )
    assert os.path.islink(os.path.join(paths["purelib"], "frontend_editables"))
