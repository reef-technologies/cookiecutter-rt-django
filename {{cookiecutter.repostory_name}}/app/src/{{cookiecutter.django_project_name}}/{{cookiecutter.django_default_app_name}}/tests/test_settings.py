import logging
from collections.abc import Generator
from importlib import import_module

import pytest
import sentry_sdk
import structlog
from sentry_sdk.integrations.logging import LoggingIntegration

from ...settings import _drop_structlog_duplicates


@pytest.fixture
def sentry_events(settings) -> Generator[list[dict]]:
    events: list[dict] = []
    client = sentry_sdk.Client(
        dsn="https://public@sentry.invalid/0",
        transport=events.append,
        default_integrations=False,
        integrations=[LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)],
        before_send=_drop_structlog_duplicates,
        before_breadcrumb=_drop_structlog_duplicates,
    )
    processor = settings.LOGGING_SENTRY_PROCESSOR
    was_active = processor.active
    processor.active = True
    try:
        with sentry_sdk.isolation_scope() as scope:
            scope.set_client(client)
            yield events
    finally:
        processor.active = was_active


def test__settings__celery_beat_schedule(settings):
    """Ensure that CELERY_BEAT_SCHEDULE points to existing tasks"""

    if not hasattr(settings, "CELERY_BEAT_SCHEDULE"):
        pytest.skip("CELERY_BEAT_SCHEDULE is not defined")

    paths = {task["task"] for task in settings.CELERY_BEAT_SCHEDULE.values()}
    for path in paths:
        module_path, task_name = path.rsplit(".", maxsplit=1)
        try:
            module = import_module(module_path)
        except ImportError:
            pytest.fail(f"The module '{module_path}' does not exist")

        if not hasattr(module, task_name):
            pytest.fail(f"The task '{task_name}' does not exist in {module_path}")


def test__settings__structlog_exceptions_reach_sentry_with_stacktrace(sentry_events):
    logger = structlog.get_logger("test")

    try:
        raise ValueError("boom")
    except ValueError:
        logger.exception("task failed")

    assert [
        (value["type"], value["value"], bool(value["stacktrace"]["frames"]))
        for event in sentry_events
        for value in event["exception"]["values"]
    ] == [("ValueError", "boom", True)]
