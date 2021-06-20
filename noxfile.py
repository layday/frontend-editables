from pathlib import Path
import sysconfig

import nox

nox.options.sessions = ["reformat", "test", "type_check"]


@nox.session(reuse_venv=True)
def reformat(session: nox.Session):
    session.install("black", "isort")
    options = ["--check"] if session.posargs == ["check"] else []
    for command in ["isort", "black"]:
        session.run(command, *options, "src", "tests", "noxfile.py")


def _install_coverage_hook(prefix: str):
    (Path(sysconfig.get_paths(vars={"base": prefix})["purelib"]) / "00-coverage.pth").write_text(
        "import coverage; coverage.process_startup()",
        encoding="utf-8",
    )


@nox.session(python=["3.6", "3.7", "3.8", "3.9", "3.10"])
def test(session: nox.Session):
    session.install(".[test]")
    _install_coverage_hook(session.virtualenv.location)
    session.run(
        *("coverage", "run", "-m", "pytest"),
        env={"COVERAGE_PROCESS_START": "pyproject.toml"},
    )
    session.run("coverage", "combine")
    session.run("coverage", "report", "--show-missing")


@nox.session
def type_check(session: nox.Session):
    session.install(".")
    session.run("npx", "pyright", external=True)


@nox.session
def build(session: nox.Session):
    git_status_output = session.run("git", "status", "--porcelain", external=True, silent=True)
    if git_status_output != "":
        session.error("tree is dirty")

    tmpdir = session.create_tmp()
    session.run("git", "clone", ".", tmpdir, external=True)
    session.chdir(tmpdir)
    session.install(
        "build",
        "flit-core @ git+https://github.com/layday/flit@fix-pep621-metadata#subdirectory=flit_core",
    )
    session.run("python", "-m", "build", "-n")
