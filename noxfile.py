"""
nox configuration for cookiecutter project template.
"""

from __future__ import annotations

import contextlib
import functools
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

import nox

CI = os.environ.get("CI") is not None

ROOT = Path(".")
PYPROJECT = nox.project.load_toml("pyproject.toml")
PYTHON_VERSION = PYPROJECT["project"]["requires-python"].strip("=~.*")

# tested default config overrides
CRUFT_TESTED_CONFIG_MATRIX = {
    "default": {},
}
CRUFT_TESTED_CONFIGS = os.getenv("CRUFT_TESTED_CONFIGS", ",".join(CRUFT_TESTED_CONFIG_MATRIX)).split(",")

nox.options.default_venv_backend = "uv"
nox.options.reuse_existing_virtualenvs = True

MD_PATHS = ["*.md"]


def get_cruft_config(config_name="default", **kw):
    with (Path(__file__).parent / "cookiecutter.json").open() as f:
        cruft_config = json.load(f)
    overrides = CRUFT_TESTED_CONFIG_MATRIX[config_name]
    complete_config = {**cruft_config, **overrides, **kw}
    config_hash = hashlib.sha256(json.dumps(complete_config, sort_keys=True).encode()).hexdigest()
    complete_config["django_project_name"] = f"{config_name}_{config_hash[:8]}"
    complete_config["repostory_name"] = complete_config["django_project_name"].replace("_", "-")
    return complete_config


@contextlib.contextmanager
def with_dirty_commit(session):
    """
    Returned context manager will commit changes to the git repository if it is dirty.

    This is needed because tools like `cruft` only use committed changes.
    """
    is_dirty = not CI and subprocess.run(["git", "diff", "--quiet"], check=False).returncode
    if is_dirty:
        with tempfile.TemporaryDirectory(prefix="rt_tmpl_repo") as tmpdir:
            session.log(f"Found dirty git repository, temporarily committing changes in {tmpdir}")
            subprocess.run(["cp", "-r", ".", tmpdir], check=True)
            with session.chdir(tmpdir):
                subprocess.run(["git", "add", "-A"], check=True)
                subprocess.run(["git", "commit", "-m", "nox: dirty commit"], check=True)
                yield
    else:
        yield


@functools.lru_cache
def _list_files() -> list[Path]:
    file_list = []
    for cmd in (
        ["git", "ls-files"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ):
        cmd_result = subprocess.run(cmd, check=True, text=True, capture_output=True)
        file_list.extend(cmd_result.stdout.splitlines())
    return [Path(p) for p in file_list]


def list_files(suffix: str | None = None) -> list[Path]:
    """List all non-files not-ignored by git."""
    file_paths = _list_files()
    if suffix is not None:
        file_paths = [p for p in file_paths if p.suffix == suffix]
    return file_paths


def run_readable(session, mode="check"):
    session.run(
        "docker",
        "run",
        "--platform",
        "linux/amd64",
        "--rm",
        "-v",
        f"{ROOT.absolute()}:/data",
        "-w",
        "/data",
        "ghcr.io/bobheadxi/readable:v0.5.0@sha256:423c133e7e9ca0ac20b0ab298bd5dbfa3df09b515b34cbfbbe8944310cc8d9c9",
        mode,
        *MD_PATHS,
        external=True,
    )


def run_shellcheck(session, mode="check"):
    shellcheck_cmd = [
        "docker",
        "run",
        "--platform",
        "linux/amd64",  # while this image is multi-arch, we cannot use digest with multi-arch images
        "--rm",
        "-v",
        f"{ROOT.absolute()}:/mnt",
        "-w",
        "/mnt",
        "-q",
        "koalaman/shellcheck:0.9.0@sha256:a527e2077f11f28c1c1ad1dc784b5bc966baeb3e34ef304a0ffa72699b01ad9c",
    ]

    files = list_files(suffix=".sh")
    if not files:
        session.log("No shell files found")
        return
    shellcheck_cmd.extend(files)

    if mode == "fmt":
        with tempfile.NamedTemporaryFile(mode="w+") as diff_file:
            session.run(
                *shellcheck_cmd,
                "--format=diff",
                external=True,
                stdout=diff_file,
                success_codes=[0, 1],
            )
            diff_file.seek(0)
            diff = diff_file.read()
            if len(diff.splitlines()) > 1:  # ignore single-line message
                session.log("Applying shellcheck patch:\n%s", diff)
                subprocess.run(
                    ["patch", "-p1"],
                    input=diff,
                    text=True,
                    check=True,
                )

    session.run(*shellcheck_cmd, external=True)


@nox.session(name="format", python=PYTHON_VERSION)
def format_(session):
    """Lint the code and apply fixes in-place whenever possible."""
    uv_env = getattr(session.virtualenv, "location", os.getenv("VIRTUAL_ENV"))
    session.run_install(
        "uv",
        "sync",
        "--locked",
        "--extra",
        "format",
        env={"UV_PROJECT_ENVIRONMENT": uv_env},
    )

    session.run("ruff", "check", "--fix", ".")
    run_shellcheck(session, mode="fmt")
    run_readable(session, mode="fmt")
    session.run("ruff", "format", ".")


@nox.session(python=PYTHON_VERSION)
def lint(session):
    """Run linters in readonly mode."""
    uv_env = getattr(session.virtualenv, "location", os.getenv("VIRTUAL_ENV"))
    session.run_install(
        "uv",
        "sync",
        "--locked",
        "--extra",
        "lint",
        env={"UV_PROJECT_ENVIRONMENT": uv_env},
    )

    session.run("ruff", "check", "--diff", "--unsafe-fixes", ".")
    session.run("codespell", ".")
    run_shellcheck(session, mode="check")
    run_readable(session, mode="check")
    session.run("ruff", "format", "--diff", ".")


@contextlib.contextmanager
def crufted_project(session, cruft_config):
    uv_env = getattr(session.virtualenv, "location", os.getenv("VIRTUAL_ENV"))
    session.run_install(
        "uv",
        "sync",
        "--locked",
        "--extra",
        "format",  # ruff is needed for the formatter hook
        env={"UV_PROJECT_ENVIRONMENT": uv_env},
    )

    tmpdir = crufted_project.tmpdir
    if not tmpdir:
        session.notify("cleanup_crufted_project")
        crufted_project.tmpdir = tmpdir = tempfile.TemporaryDirectory(prefix="rt_crufted_")
    tmpdir_path = Path(tmpdir.name)
    tmpdir_path.mkdir(exist_ok=True)

    project_path = tmpdir_path / cruft_config["repostory_name"]
    if not project_path.exists():
        session.log("Creating project in %s", tmpdir.name)
        with with_dirty_commit(session):
            session.run(
                "cruft",
                "create",
                ".",
                "--output-dir",
                str(tmpdir_path),
                "--no-input",
                "--extra-context",
                json.dumps(cruft_config),
            )
        with session.chdir(project_path):
            session.run("git", "init", external=True)
            session.run("./setup-dev.sh", external=True)

    with session.chdir(project_path):
        yield project_path


crufted_project.tmpdir = None


def rm_root_owned(session, dirpath):
    assert not ROOT.is_relative_to(dirpath)  # sanity check before we nuke dirpath
    children = sorted(dirpath.iterdir())
    session.run(
        "docker",
        "run",
        "--rm",
        "-v",
        f"{dirpath}:/tmpdir/",
        "alpine:3.18.0",
        "rm",
        "-rf",
        *[f"/tmpdir/{f.name}" for f in children],
        external=True,
    )


@contextlib.contextmanager
def docker_up(session):
    session.run("docker", "compose", "up", "-d")
    try:
        yield
    finally:
        session.run("docker", "compose", "down", "-v", "--remove-orphans")


@nox.session(python=PYTHON_VERSION, tags=["crufted_project"])
@nox.parametrize("cruft_config_name", CRUFT_TESTED_CONFIGS)
def lint_crufted_project(session, cruft_config_name):
    cruft_config = get_cruft_config(cruft_config_name)
    with crufted_project(session, cruft_config):
        session.run("nox", "-s", "lint")  # TODO: RT-49 re-enable 'type_check'


@nox.session(python=PYTHON_VERSION, tags=["crufted_project"])
@nox.parametrize("cruft_config_name", CRUFT_TESTED_CONFIGS)
def test_crufted_project(session, cruft_config_name):
    cruft_config = get_cruft_config(cruft_config_name)
    with crufted_project(session, cruft_config):
        with docker_up(session):
            session.run("nox", "-s", "test")


@nox.session(python=PYTHON_VERSION)
def cleanup_crufted_project(session):
    if crufted_project.tmpdir:
        # workaround for docker compose creating root-owned files
        rm_root_owned(session, Path(crufted_project.tmpdir.name))
        crufted_project.tmpdir.cleanup()
        crufted_project.tmpdir = None
