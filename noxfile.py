from pathlib import Path
import sysconfig

import nox


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
