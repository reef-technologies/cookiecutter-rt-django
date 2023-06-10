import os
from pathlib import Path

import nox

CI = os.environ.get('CI') is not None

ROOT = Path('.')
PYTHON_VERSIONS = ['3.9']
PYTHON_DEFAULT_VERSION = PYTHON_VERSIONS[-1]
APP_ROOT = ROOT / 'app' / 'src'

nox.options.default_venv_backend = 'venv'
nox.options.stop_on_first_error = True
nox.options.reuse_existing_virtualenvs = True

# In CI, use Python interpreter provided by GitHub Actions
if CI:
    nox.options.force_venv_backend = 'none'


def run_readable(session, mode="fmt"):
    session.run(
        'docker',
        'run',
        '--rm',
        '-v', f'{ROOT.absolute()}:/data',
        '-w', '/data',
        '-u', f'{os.geteuid()}:{os.getegid()}',
        'ghcr.io/bobheadxi/readable:v0.5.0@sha256:423c133e7e9ca0ac20b0ab298bd5dbfa3df09b515b34cbfbbe8944310cc8d9c9',
        mode, '![.]**/*.md',
    )


@nox.session(name='format', python=PYTHON_DEFAULT_VERSION)
def format_(session):
    session.run('pip', 'install', '-e', '.[format]')
    session.run('ruff', 'check', '--fix', '.')
    run_readable(session, mode="fmt")


@nox.session(python=PYTHON_DEFAULT_VERSION)
def lint(session):
    session.run('pip', 'install', '-e', '.[lint]')
    session.run('ruff', 'check', '--diff', '.')
    run_readable(session, mode="check")


@nox.session(python=PYTHON_DEFAULT_VERSION)
def type_check(session):
    session.run('pip', 'install', '-e', '.[type_check]')
    with session.chdir(str(APP_ROOT)):
        session.run(
            'mypy',
            '--config-file', 'mypy.ini',
            '.',
            *session.posargs
        )


@nox.session(python=PYTHON_DEFAULT_VERSION)
def security_check(session):
    session.run('pip', 'install', 'bandit')
    with session.chdir(str(APP_ROOT)):
        session.run(
            'bandit',
            '--ini', 'bandit.ini',
            '-x', 'requirements_freeze.py',
            '-r',
            '.',
            *session.posargs
        )


@nox.session(python=PYTHON_VERSIONS)
def test(session):
    with session.chdir(str(APP_ROOT)):
        session.run(
            'pip', 'install', '-r', 'requirements.txt',
            'pytest',
            'pytest-django',
            'pytest-xdist',
            'ipdb',
            'freezegun',
        )
        session.run(
            'pytest',
            '-W', 'ignore::DeprecationWarning', '-s', '-x', '-vv',
            '-n', 'auto',
            '{{cookiecutter.django_project_name}}',
            *session.posargs,
            env={
                'DJANGO_SETTINGS_MODULE': '{{cookiecutter.django_project_name}}.settings',
                'DEBUG_TOOLBAR': '0',
            },
        )
