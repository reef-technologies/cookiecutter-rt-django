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


@nox.session(python=PYTHON_DEFAULT_VERSION)
def lint(session):
    session.run('pip', 'install', 'flake8')
    with session.chdir(str(APP_ROOT)):
        session.run('flake8', '--ignore', 'E501', '.')


@nox.session(python=PYTHON_DEFAULT_VERSION)
def type_check(session):
    with session.chdir(str(APP_ROOT)):
        session.run(
            'pip', 'install', '-r', 'requirements.txt',
            'mypy',
            'django-stubs[compatible-mypy]',
            'types-requests',
            'types-python-dateutil',
            'types-freezegun',
            'djangorestframework-stubs[compatible-mypy]',
        )
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
