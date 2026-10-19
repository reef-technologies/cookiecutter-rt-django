"""Start memray at interpreter start when ``MEMORY_PROFILING=1``.

``sitecustomize.py`` next to this file imports it in every Python process of the
production image, before any application code runs (the image puts ``/root/src`` on
``PYTHONPATH``, which is how Python finds ``sitecustomize``).  Nothing here touches
Django or the project: it only decides, from the command line, whether this process
is worth profiling and, if so, starts a memray tracker that follows forks, so gunicorn
workers and celery pool children get capture files of their own.

Captures land in ``PROFILES_DIR`` (bind-mounted from ``./profiles`` on the host) as
``<role>-<hostname>-<pid>-<utc timestamp>.bin``; forked children append their pid.
See the "Memory profiling" section of the README for how to read them.
"""

from __future__ import annotations

import os
import socket
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import memray

PROFILES_DIR = Path("/var/profiles")

# `manage.py` commands that run and exit; profiling them would only litter PROFILES_DIR.
SKIPPED_MANAGE_COMMANDS = frozenset(
    {
        "changepassword",
        "check",
        "collectstatic",
        "createsuperuser",
        "dbshell",
        "dumpdata",
        "flush",
        "loaddata",
        "makemigrations",
        "migrate",
        "shell",
        "shell_plus",
        "showmigrations",
        "sqlmigrate",
        "test",
        "wait_for_database",
    }
)
# Every celery subcommand, so the one on the command line can be told apart from option
# values and queue names; only the long-running ones are profiled.
CELERY_COMMANDS = frozenset(
    {
        "amqp",
        "beat",
        "call",
        "control",
        "events",
        "flower",
        "graph",
        "inspect",
        "list",
        "logtool",
        "migrate",
        "multi",
        "purge",
        "report",
        "result",
        "shell",
        "status",
        "upgrade",
        "worker",
    }
)
PROFILED_CELERY_COMMANDS = frozenset({"beat", "flower", "worker"})
# Scripts that never run for long.
SKIPPED_PROGRAMS = frozenset({"healthcheck.py", "memray"})

# Options that take a value in the next argument, so the parsers know to step over it.
_INTERPRETER_OPTIONS_WITH_VALUE = frozenset({"-W", "-X", "--check-hash-based-pycs"})
_CELERY_OPTIONS_WITH_VALUE = frozenset(
    {"-A", "--app", "-b", "--broker", "--result-backend", "--loader", "--config", "--workdir"}
)

_tracker: memray.Tracker | None = None


def split_command_line(orig_argv: list[str]) -> tuple[str | None, list[str]]:
    """Return ``(program, args)`` for an interpreter command line such as ``sys.orig_argv``.

    ``program`` is the module name after ``-m``, ``"-c"`` for inline code, or the basename
    of the script; ``args`` is everything after it.  ``(None, [])`` when there is no program
    at all, i.e. an interactive interpreter or a script read from stdin.
    """
    i = 1
    while i < len(orig_argv):
        arg = orig_argv[i]
        if arg == "-m":
            if i + 1 >= len(orig_argv):
                return None, []
            return orig_argv[i + 1], orig_argv[i + 2 :]
        if arg == "-c":
            return "-c", orig_argv[i + 1 :]
        if arg in _INTERPRETER_OPTIONS_WITH_VALUE:
            i += 2
            continue
        if arg.startswith("-"):  # any other interpreter option, including "-" for stdin
            i += 1
            continue
        return os.path.basename(arg), orig_argv[i + 1 :]
    return None, []


def _celery_command(args: list[str]) -> str | None:
    skip_next = False
    for arg in args:
        if skip_next:
            skip_next = False
        elif arg in _CELERY_OPTIONS_WITH_VALUE:
            skip_next = True
        elif arg in CELERY_COMMANDS:
            return arg
    return None


def _option_value(args: list[str], *names: str) -> str | None:
    for i, arg in enumerate(args):
        if arg in names and i + 1 < len(args):
            return args[i + 1]
        for name in names:
            if arg.startswith(name + "="):
                return arg[len(name) + 1 :]
    return None


def role_for(orig_argv: list[str]) -> str | None:
    """Name the role of a process from its command line, or ``None`` if it is not profiled."""
    program, args = split_command_line(orig_argv)
    if program is None or program in SKIPPED_PROGRAMS:
        return None
    if program == "-c":
        code = args[0] if args else ""
        if "multiprocessing.forkserver" in code:
            return "multiprocessing-forkserver"
        if "multiprocessing.spawn" in code:
            return "multiprocessing-spawn"
        return "python-c"
    if program == "manage.py":
        command = args[0] if args else None
        if command is None or command.startswith("-") or command in SKIPPED_MANAGE_COMMANDS:
            return None
        return f"manage-{command}"
    if program == "celery":
        command = _celery_command(args)
        if command not in PROFILED_CELERY_COMMANDS or "--detach" in args or "-D" in args:
            return None
        node = _option_value(args, "-n", "--hostname") if command == "worker" else None
        return f"celery-{node.split('@')[0]}" if node else f"celery-{command}"
    return program


def start(role: str) -> Path:
    """Start tracking this process into a new capture file and return the file's path."""
    global _tracker
    import memray  # deferred: only the processes that are profiled pay for the import

    if not PROFILES_DIR.is_dir():
        raise FileNotFoundError(f"{PROFILES_DIR} does not exist (is it mounted?)")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = PROFILES_DIR / f"{role}-{socket.gethostname()}-{os.getpid()}-{stamp}.bin"
    # trace_python_allocators: record pymalloc's small-object allocations individually, so a
    # leak of many small objects is attributed to the line that created them; costs bigger
    # captures and more overhead than memray's default, which only sees pymalloc's arenas.
    tracker = memray.Tracker(path, follow_fork=True, trace_python_allocators=True)
    tracker.__enter__()
    _tracker = tracker
    return path


def stop() -> None:
    """Stop tracking and finish the capture file.

    Optional: a capture is readable even if the process exits, or is killed, without this.
    """
    global _tracker
    if _tracker is not None:
        _tracker.__exit__(None, None, None)
        _tracker = None


def autostart() -> None:
    """Profile this process when ``MEMORY_PROFILING=1`` and the command line qualifies."""
    if os.environ.get("MEMORY_PROFILING") != "1":
        return

    if not (role := role_for(sys.orig_argv)):
        return

    try:
        path = start(role)
        print(f"memray_autostart: profiling {role} -> {path}", file=sys.stderr)
    except Exception as exc:  # profiling must never take the process down
        print(f"memray_autostart: not profiling {role}: {exc}", file=sys.stderr)
