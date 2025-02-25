{%- if cookiecutter.use_celery == 'y' -%}
import logging
import os

from celery import Celery
{%- if cookiecutter.monitoring == "y" %}
from celery.signals import setup_logging, worker_process_shutdown
{% endif -%}
from django.conf import settings
from django_structlog.celery.steps import DjangoStructLogInitStep
from more_itertools import chunked
{%- if cookiecutter.monitoring == "y" %}
from prometheus_client import Gauge, multiprocess
{% endif %}
from .settings import configure_structlog

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{cookiecutter.django_project_name}}.settings")

app = Celery("{{cookiecutter.django_project_name}}")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.steps["worker"].add(DjangoStructLogInitStep)
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

{%- if cookiecutter.monitoring == "y" %}
num_tasks_in_queue = Gauge(
    "celery_queue_len",
    "How many tasks are there in a queue",
    labelnames=("queue",),
)
{% endif %}


@setup_logging.connect
def receiver_setup_logging(loglevel, logfile, format, colorize, **kwargs):  # pragma: no cover
    config = settings.LOGGING
    # worker and master have a logfile, beat does not
    if logfile:
        config["handlers"]["console"]["class"] = "logging.FileHandler"
        config["handlers"]["console"]["filename"] = logfile
    logging.config.dictConfig(config)
    configure_structlog()


def get_tasks_in_queue(queue_name: str) -> list[bytes]:
    with app.pool.acquire(block=True) as conn:
        return conn.default_channel.client.lrange(queue_name, 0, -1)


def get_num_tasks_in_queue(queue_name: str) -> int:
    with app.pool.acquire(block=True) as conn:
        return conn.default_channel.client.llen(queue_name)


def move_tasks(source_queue: str, destination_queue: str, chunk_size: int = 100) -> None:
    with app.pool.acquire(block=True) as conn:
        client = conn.default_channel.client
        tasks = client.lrange(source_queue, 0, -1)

        for chunk in chunked(tasks, chunk_size):
            with client.pipeline() as pipe:
                for task in chunk:
                    client.rpush(destination_queue, task)
                    client.lrem(source_queue, 1, task)
                pipe.execute()


def flush_tasks(queue_name: str) -> None:
    with app.pool.acquire(block=True) as conn:
        conn.default_channel.client.delete(queue_name)

{% if cookiecutter.monitoring == "y" %}
@worker_process_shutdown.connect
def child_exit(pid, **kw):
    multiprocess.mark_process_dead(pid)
{% endif -%}
{% else %}
# Use this as a starting point for your project with celery.
# If you are not using celery, you can remove this app
{% endif -%}
