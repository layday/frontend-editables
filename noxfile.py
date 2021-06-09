import nox


@nox.session(python=["3.6", "3.7", "3.8", "3.9"])
def test(session: nox.Session):
    session.install(".[test]")
    session.run("coverage", "run", "-m", "pytest")
    session.run("coverage", "report", "-m")


@nox.session
def type_check(session: nox.Session):
    session.install(".")
    session.run("npx", "-y", "pyright", external=True)
