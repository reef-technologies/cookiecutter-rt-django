from __future__ import annotations

from contextlib import suppress
import functools
import os
import platform
import subprocess
import tempfile
from pathlib import Path
import nox
from nox.command import CommandFailed

CI = os.environ.get("CI") is not None

ROOT = Path(".")
PYPROJECT = nox.project.load_toml("pyproject.toml")
PYTHON_VERSION = PYPROJECT["project"]["requires-python"].strip("=~.*")
APP_ROOT = ROOT / "app" / "src"
SHELLCHECK_IMAGE = "koalaman/shellcheck:v0.9.0"
SHELLCHECK_DIGESTS = {
    "amd64": "sha256:a527e2077f11f28c1c1ad1dc784b5bc966baeb3e34ef304a0ffa72699b01ad9c",
    "arm64": "sha256:beab2609164b01e8f90993c257fd2da5e09dfba23aa58f1acb1a3d2619909a46",
}
SHELLCHECK_ARCH_ALIASES = {
    "amd64": "amd64",
    "x86_64": "amd64",
    "arm64": "arm64",
    "aarch64": "arm64",
}

nox.options.default_venv_backend = "uv"
nox.options.stop_on_first_error = True
nox.options.reuse_existing_virtualenvs = not CI


def install(session: nox.Session, *args):
    groups = []
    for arg in args:
        groups.extend(["--group", arg])

    uv_env = getattr(session.virtualenv, "location", os.getenv("VIRTUAL_ENV"))
    session.run_install(
        "uv",
        "sync",
        "--locked",
        *groups,
        env={"UV_PROJECT_ENVIRONMENT": uv_env},
    )


@functools.lru_cache
def _list_files() -> list[Path]:
    file_list = []
    for cmd in (
        ["git", "ls-files"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ):
        cmd_result = subprocess.run(cmd, check=True, text=True, capture_output=True)
        file_list.extend(cmd_result.stdout.splitlines())
    file_paths = [Path(p) for p in file_list]
    return file_paths


def list_files(suffix: str | None = None) -> list[Path]:
    """List all non-files not-ignored by git."""
    file_paths = _list_files()
    if suffix is not None:
        file_paths = [p for p in file_paths if p.suffix == suffix]
    return file_paths


def shellcheck_platform_image(machine: str | None = None) -> tuple[str, str]:
    detected_machine = (machine or platform.machine()).lower()
    arch = SHELLCHECK_ARCH_ALIASES.get(detected_machine)
    if arch is None:
        supported = ", ".join(sorted(SHELLCHECK_ARCH_ALIASES))
        raise RuntimeError(f"Unsupported shellcheck platform {detected_machine!r}; supported machines: {supported}")

    digest = SHELLCHECK_DIGESTS[arch]
    return f"linux/{arch}", f"{SHELLCHECK_IMAGE}@{digest}"


def run_shellcheck(session, mode="check"):
    shellcheck_platform, shellcheck_image = shellcheck_platform_image()
    shellcheck_cmd = [
        "docker",
        "run",
        "--platform",
        shellcheck_platform,
        "--rm",
        "-v",
        f"{ROOT.absolute()}:/mnt",
        "-w",
        "/mnt",
        "-q",
        shellcheck_image,
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
    install(session, "format")
    session.run("ruff", "check", "--fix", ".")
    run_shellcheck(session, mode="fmt")
    session.run("ruff", "format", ".")


@nox.session(python=PYTHON_VERSION)
def lint(session):
    """Run linters in readonly mode."""
    install(session, "lint")
    session.run("ruff", "check", "--diff", "--unsafe-fixes", ".")
    session.run("codespell", ".")
    run_shellcheck(session, mode="check")
    session.run("ruff", "format", "--diff", ".")


@nox.session(python=PYTHON_VERSION)
def type_check(session):
    install(session, "type_check")
    with session.chdir(str(APP_ROOT)):
        session.run("mypy", "--config-file", "mypy.ini", ".", *session.posargs)


@nox.session(python=PYTHON_VERSION)
def check_missing_migrations(session):
    install(session, "check_missing_migrations")
    session.run(
        "django-admin",
        "makemigrations",
        "--dry-run",
        "--check",
        env={"DJANGO_SETTINGS_MODULE": "{{ cookiecutter.django_project_name }}.settings"},
    )


@nox.session(python=PYTHON_VERSION)
def test(session):
    install(session, "test")
    with session.chdir(str(APP_ROOT)):
        session.run(
            "pytest",
            "-W",
            "ignore::DeprecationWarning",
            "-s",
            "-x",
            "-vv",
            "-n",
            "auto",
            "{{cookiecutter.django_project_name}}",
            *session.posargs,
        )


VERSION_TAG_PATTERN = "v[0-9]+.[0-9]+.[0-9]+"


def _get_last_tag(session: nox.Session) -> str | None:
    with suppress(CommandFailed):
        return session.run("git", "describe", "--tags", "--abbrev=0", "--match", VERSION_TAG_PATTERN, "HEAD^", silent=True, external=True).strip()


def _get_base_branch() -> str:
    if os.environ.get("GITHUB_ACTIONS"):
        return os.environ["GITHUB_BASE_REF"]
    return "master"


def _get_current_branch(session: nox.Session) -> str:
    if os.environ.get("GITHUB_ACTIONS"):
        return os.environ["GITHUB_HEAD_REF"]
    return session.run("git", "branch", "--show-current", silent=True, external=True).strip()


def _get_current_tag(session: nox.Session) -> str | None:
    with suppress(CommandFailed):
        return session.run("git", "describe", "--tags", "--abbrev=0", "--match", VERSION_TAG_PATTERN, "--exact-match", silent=True, external=True).strip()


def _truncate(text: str, *, limit: int) -> str:
    if len(text) <= limit:
        return text

    lines = text.splitlines(keepends=True)
    accumulated_length = 0
    for i, line in enumerate(lines):
        accumulated_length += len(line)
        if accumulated_length > limit:
            return "".join(lines[:i]) + "\n… (truncated)\n"

    assert False


@nox.session(python=PYTHON_VERSION)
def check_commits(session: nox.Session):
    """
    Verify:
    - commits match the Conventional Commits format
    - branches are squashed before merging
    - no merge commits, FF or rebase only
    """

    install(session, "commits_check")

    # check that commits since last tag (or all commits if no tags) match the Conventional Commits format
    command = ["cz", "check"]
    if last_tag := _get_last_tag(session):
        command += ["--rev-range", f"{last_tag}..HEAD"]
    session.run(*command)

    # check that there are no merge commits, FF or rebase only
    if merge_commits := session.run("git", "rev-list", "--merges", f"{last_tag}..HEAD" if last_tag else "HEAD", silent=True, external=True).strip():
        session.error(f"Merge commits found:\n{merge_commits}")

    # check that if on a branch, it has been squashed before merging
    base_branch = _get_base_branch()
    current_branch = _get_current_branch(session)
    if current_branch and current_branch != base_branch:
        num_commits = int(session.run("git", "rev-list", "--count", f"{base_branch}..HEAD", silent=True, external=True).strip())
        if num_commits > 1:
            session.error(f"Branch '{current_branch}' has {num_commits} commits since diverging from '{base_branch}'. Please squash your commits before merging.")


@nox.session(python=PYTHON_VERSION)
def publish_changelog(session: nox.Session):
    import requests

    if not _get_current_tag(session):
        return

    try:
        slack_channel = os.environ["SLACK_CHANGELOG_CHANNEL"]
        slack_webhook_url = os.environ["SLACK_WEBHOOK_URL"]
    except KeyError:
        session.error("SLACK_CHANGELOG_CHANNEL and SLACK_WEBHOOK_URL environment variables are required to publish changelog to Slack. Skipping.")

    install(session, "commits_check")

    command = ["cz", "changelog", "--dry-run"]
    if last_tag := _get_last_tag(session):
        command += ["--start-rev", last_tag]
    changelog = session.run(*command, silent=True)

    # Slack block `mrkdwn` text limit is 3000 chars; keep under it
    changelog_trimmed = _truncate(changelog, limit=2500)
    payload = {
        "channel": slack_channel,
        "text": f"```{changelog_trimmed}```",
    }

    response = requests.post(slack_webhook_url, json=payload, timeout=15)
    response.raise_for_status()
