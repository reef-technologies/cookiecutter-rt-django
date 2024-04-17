{%- if cookiecutter.use_celery == 'y' -%}
import logging
import os

from celery import Celery
{%- if cookiecutter.monitoring == "y" %}
from celery.signals import setup_logging, worker_process_shutdown
{% endif -%}
from django.conf import settings
from django_structlog.celery.steps import DjangoStructLogInitStep
{%- if cookiecutter.monitoring == "y" %}
from prometheus_client import multiprocess
{% endif %}
from .settings import configure_structlog

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{cookiecutter.django_project_name}}.settings")

app = Celery("{{cookiecutter.django_project_name}}")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.steps["worker"].add(DjangoStructLogInitStep)
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@setup_logging.connect
def receiver_setup_logging(loglevel, logfile, format, colorize, **kwargs):  # pragma: no cover
    logging.config.dictConfig(settings.LOGGING)
    configure_structlog()


def route_task(name, args, kwargs, options, task=None, **kw):
    return {"queue": "celery"}
{% if cookiecutter.monitoring == "y" %}

@worker_process_shutdown.connect
def child_exit(pid, **kw):
    multiprocess.mark_process_dead(pid)
{% endif -%}
{% else %}
# Use this as a starting point for your project with celery.
# If you are not using celery, you can remove this app
{% endif -%}
