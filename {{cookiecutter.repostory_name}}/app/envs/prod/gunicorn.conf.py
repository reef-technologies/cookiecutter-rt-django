import multiprocessing

import environ
{% if cookiecutter.monitoring == "y" %}
from prometheus_client import multiprocess
{% endif %}

env = environ.Env()

workers = env.int("GUNICORN_WORKERS", 2 * multiprocessing.cpu_count() + 1)
max_workers = env.int("GUNICORN_MAX_WORKERS", 0)
if max_workers > 0:
    workers = min(max_workers, workers)
threads = env.int("GUNICORN_THREADS", 1)
preload_app = env.bool("GUNICORN_PRELOAD_APP", True)
bind = "unix:/var/run/gunicorn/gunicorn.sock"
{% if cookiecutter.use_channels == "y" %}
wsgi_app = "{{ cookiecutter.django_project_name }}.asgi:application"
{% else %}
wsgi_app = "{{ cookiecutter.django_project_name }}.wsgi:application"
{% endif %}
access_logfile = "-"
{% if cookiecutter.use_channels == "y" %}
worker_class = "uvicorn.workers.UvicornWorker"
{% endif %}


{% if cookiecutter.monitoring == "y" %}
def child_exit(server, worker):
    multiprocess.mark_process_dead(worker.pid)
{% endif %}
