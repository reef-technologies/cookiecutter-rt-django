"""Tests for the memory profiling hook in ``app/src/memray_autostart.py``."""

import os
import sys

import pytest

import memray_autostart

# memray has no Windows build (pyproject excludes it there); skip this file instead of erroring
memray = pytest.importorskip("memray")

PYTHON = "/root/src/.venv/bin/python"
BIN = "/root/src/.venv/bin"


@pytest.mark.parametrize(
    ("orig_argv", "role"),
    [
        # servers, however they were started
        ([PYTHON, f"{BIN}/gunicorn", "-c", "gunicorn.conf.py"], "gunicorn"),
        ([PYTHON, "-m", "celery", "worker", "-n", "master@abc", "-Q", "celery"], "celery-master"),
        ([PYTHON, "-m", "celery", "worker", "-n", "worker@abc", "-Q", "worker"], "celery-worker"),
        ([PYTHON, f"{BIN}/celery", "-A", "project", "beat", "-l", "INFO"], "celery-beat"),
        ([PYTHON, f"{BIN}/celery", "--app=project", "--broker=redis://r", "flower"], "celery-flower"),
        ([PYTHON, "-u", "-X", "dev", "-m", "celery", "-A", "project", "beat"], "celery-beat"),
        ([PYTHON, "./manage.py", "sync_extrinsics"], "manage-sync_extrinsics"),
        ([PYTHON, f"{BIN}/dagster-webserver", "-p", "3000", "--path-prefix", "/dagster"], "dagster-webserver"),
        ([PYTHON, "-c", "print(1)"], "python-c"),
        ([PYTHON, "-c", "from multiprocessing.forkserver import main; main(1)"], "multiprocessing-forkserver"),
        ([PYTHON, "-c", "from multiprocessing.spawn import spawn_main; spawn_main(1)"], "multiprocessing-spawn"),
        # short-lived processes
        ([PYTHON, "-m", "celery", "worker", "--detach", "-n", "master@abc"], None),
        ([PYTHON, "-m", "celery", "worker", "-D", "-n", "master@abc"], None),
        ([PYTHON, f"{BIN}/celery", "-A", "project", "status"], None),
        ([PYTHON, f"{BIN}/celery", "-A", "worker", "status"], None),  # a project called "worker"
        ([PYTHON, f"{BIN}/celery", "multi", "start", "master", "worker"], None),
        ([PYTHON, "./manage.py", "migrate"], None),
        ([PYTHON, "./manage.py", "wait_for_database", "--timeout", "10"], None),
        ([PYTHON, "./manage.py", "--version"], None),
        ([PYTHON, "./manage.py"], None),
        ([PYTHON, "./healthcheck.py", "/var/run/gunicorn/gunicorn.sock"], None),
        ([PYTHON, f"{BIN}/memray", "flamegraph", "x.bin"], None),
        ([PYTHON], None),
        ([PYTHON, "-"], None),
    ],
)
def test_role_for(orig_argv, role):
    assert memray_autostart.role_for(orig_argv) == role


@pytest.fixture
def profiles_dir(monkeypatch, tmp_path):
    monkeypatch.setattr(memray_autostart, "PROFILES_DIR", str(tmp_path))
    yield tmp_path
    memray_autostart.stop()


def test_autostart_profiles_a_qualifying_process(monkeypatch, profiles_dir):
    monkeypatch.setenv("MEMORY_PROFILING", "1")
    monkeypatch.setattr(sys, "orig_argv", [PYTHON, f"{BIN}/gunicorn", "-c", "gunicorn.conf.py"])

    memray_autostart.autostart()
    junk = [bytearray(1024) for _ in range(100)]
    memray_autostart.stop()

    (capture,) = profiles_dir.iterdir()
    assert capture.name.startswith("gunicorn-")
    assert capture.name.endswith(".bin")
    reader = memray.FileReader(capture)
    assert reader.metadata.pid == os.getpid()
    assert any(True for _ in reader.get_allocation_records())
    assert len(junk) == 100


def test_autostart_does_nothing_when_disabled(monkeypatch, profiles_dir):
    monkeypatch.delenv("MEMORY_PROFILING", raising=False)
    monkeypatch.setattr(sys, "orig_argv", [PYTHON, f"{BIN}/gunicorn", "-c", "gunicorn.conf.py"])

    memray_autostart.autostart()

    assert list(profiles_dir.iterdir()) == []


def test_autostart_does_nothing_for_a_skipped_process(monkeypatch, profiles_dir):
    monkeypatch.setenv("MEMORY_PROFILING", "1")
    monkeypatch.setattr(sys, "orig_argv", [PYTHON, f"{BIN}/celery", "-A", "project", "status"])

    memray_autostart.autostart()

    assert list(profiles_dir.iterdir()) == []


def test_autostart_reports_a_missing_profiles_dir_instead_of_raising(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("MEMORY_PROFILING", "1")
    monkeypatch.setattr(memray_autostart, "PROFILES_DIR", str(tmp_path / "missing"))
    monkeypatch.setattr(sys, "orig_argv", [PYTHON, f"{BIN}/gunicorn", "-c", "gunicorn.conf.py"])

    memray_autostart.autostart()

    assert "not profiling gunicorn" in capsys.readouterr().err
    assert not (tmp_path / "missing").exists()
