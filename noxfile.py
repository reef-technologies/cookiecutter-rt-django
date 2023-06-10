"""
nox configuration for cookiecutter project template.
"""

import contextlib
import os
import tempfile
from pathlib import Path

import nox

CI = os.environ.get('CI') is not None

ROOT = Path('.')
PYTHON_VERSIONS = ['3.9']
PYTHON_DEFAULT_VERSION = PYTHON_VERSIONS[-1]

nox.options.default_venv_backend = 'venv'
nox.options.reuse_existing_virtualenvs = True


# In CI, use Python interpreter provided by GitHub Actions
if CI:
    nox.options.force_venv_backend = 'none'


CRUFTED_PROJECT_TMPDIR = None

MD_PATHS = ['*.md']


def run_readable(session, mode="fmt"):
    session.run(
        'docker',
        'run',
        '--rm',
        '-v', f'{ROOT.absolute()}:/data',
        '-w', '/data',
        '-u', f'{os.geteuid()}:{os.getegid()}',
        'ghcr.io/bobheadxi/readable:v0.5.0@sha256:423c133e7e9ca0ac20b0ab298bd5dbfa3df09b515b34cbfbbe8944310cc8d9c9',
        mode, *MD_PATHS
    )


@nox.session(name='format', python=PYTHON_DEFAULT_VERSION)
def format_(session):
    """Lint the code and apply fixes in-place whenever possible."""
    session.run('pip', 'install', '-e', '.[format]')
    session.run('ruff', 'check', '--fix', '.')
    run_readable(session, mode="fmt")


@nox.session(python=PYTHON_DEFAULT_VERSION)
def lint(session):
    """Run linters in readonly mode."""
    session.run('pip', 'install', '-e', '.[lint]')
    session.run('ruff', 'check', '.')
    run_readable(session, mode="check")


@contextlib.contextmanager
def crufted_project(session):
    session.run("pip", "install", "-e", ".")
    global CRUFTED_PROJECT_TMPDIR
    if not CRUFTED_PROJECT_TMPDIR:
        CRUFTED_PROJECT_TMPDIR = tempfile.TemporaryDirectory(prefix="rt-crufted_")
        session.log("Creating project in %s", CRUFTED_PROJECT_TMPDIR.name)
        session.run("cruft", "create", ".", "--output-dir", CRUFTED_PROJECT_TMPDIR.name, "--no-input")
        session.notify('cleanup_crufted_project')
    project_path = Path(CRUFTED_PROJECT_TMPDIR.name) / "project"
    session.chdir(project_path)
    yield project_path
    session.chdir(ROOT)


def rm_root_owned(session, dirpath):
    assert not ROOT.is_relative_to(dirpath)  # sanity check before we nuke dirpath
    session.run("docker", "run", "--rm", "-v", f"{dirpath}:/tmpdir/", "alpine:3.18.0", "rm", "-rf", "/tmpdir/project")


@contextlib.contextmanager
def docker_up(session):
    session.run("docker-compose", "up", "-d")
    yield
    session.run("docker-compose", "down", "-v", "--remove-orphans")


@nox.session(python=PYTHON_DEFAULT_VERSION, tags=["crufted_project"])
def lint_crufted_project(session):
    with crufted_project(session):
        session.run('nox', '-s', 'lint')


@nox.session(python=PYTHON_DEFAULT_VERSION, tags=["crufted_project"])
def test_crufted_project(session):
    with crufted_project(session):
        session.run('./setup-dev.sh')
        with docker_up(session):
            session.run('nox', '-s', 'test')


@nox.session(python=PYTHON_DEFAULT_VERSION)
def cleanup_crufted_project(session):
    global CRUFTED_PROJECT_TMPDIR
    if CRUFTED_PROJECT_TMPDIR:
        # workaround for docker-compose creating root-owned files
        rm_root_owned(session, CRUFTED_PROJECT_TMPDIR.name)
        CRUFTED_PROJECT_TMPDIR.cleanup()
        CRUFTED_PROJECT_TMPDIR = None

