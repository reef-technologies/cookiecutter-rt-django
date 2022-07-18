import nox
from pathlib import Path


ROOT = Path('.')
PYTHON_VERSIONS = ['3.9']
APP_ROOT = ROOT / 'app' / 'src'

nox.options.default_venv_backend = 'venv'
nox.options.stop_on_first_error = True
nox.options.reuse_existing_virtualenvs = True


@nox.session(python=PYTHON_VERSIONS)
def lint(session):
    session.install('flake8')
    with session.chdir(str(APP_ROOT)):
        session.run('flake8', '--ignore', 'E501', '.')


@nox.session(python=PYTHON_VERSIONS)
def type_check(session):
    with session.chdir(str(APP_ROOT)):
        session.install(
            '-r', 'requirements.txt',
            'mypy',
            'django-stubs[compatible-mypy]',
            'types-requests',
            'types-python-dateutil',
            'djangorestframework-stubs[compatible-mypy]',
        )
        session.run('mypy', '.')


@nox.session(python=PYTHON_VERSIONS)
def security_check(session):
    session.install('bandit')
    with session.chdir(str(APP_ROOT)):
        session.run('bandit', '--ini', 'bandit.ini', '-r', '.')


@nox.session(python=PYTHON_VERSIONS)
def test(session):
    with session.chdir(str(APP_ROOT)):
        session.install(
            '-r', 'requirements.txt',
            'pytest',
            'pytest-django',
            'ipdb',
            'freezegun',
        )
        session.run(
            'pytest',
            '-W', 'ignore::DeprecationWarning', '-s', '-x', '-vv',
            'project',
            *session.posargs,
            env={
                'DJANGO_SETTINGS_MODULE': '{{cookiecutter.django_project_name}}.settings',
                'DEBUG_TOOLBAR': '0',
            },
        )
