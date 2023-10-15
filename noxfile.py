import nox


@nox.session
def pre_commit(session):
    poetry_cmd = "poetry install --with dev --no-root"
    session.run(*poetry_cmd.split(), external=True)
    session.run("pre-commit", "run", "--all-files")


@nox.session
def test(session):
    poetry_cmd = "poetry install --with test"
    session.run(*poetry_cmd.split(), external=True)
    pytest = "pytest --cov-report term-missing:skip-covered --cov=btclib_node"
    session.run(*pytest.split())
