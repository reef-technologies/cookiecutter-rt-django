import multiprocessing
{% if cookiecutter.monitoring == "y" %}
from prometheus_client import multiprocess
{% endif %}
workers = 2 * multiprocessing.cpu_count() + 1
bind = "0.0.0.0:8000"
{%- if cookiecutter.use_channels == "y" %}
wsgi_app = "{{ cookiecutter.django_project_name }}.asgi:application"
{%- else %}
wsgi_app = "{{ cookiecutter.django_project_name }}.wsgi:application"
{%- endif %}
access_logfile = "-"
{%- if cookiecutter.use_channels == "y" %}
worker_class = "uvicorn.workers.UvicornWorker"
{%- endif %}


{% if cookiecutter.monitoring == "y" -%}
def child_exit(server, worker):
    multiprocess.mark_process_dead(worker.pid)
{%- endif %}
