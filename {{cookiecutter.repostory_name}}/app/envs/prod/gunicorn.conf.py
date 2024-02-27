import multiprocessing
{% if cookiecutter.monitoring == "y" %}
from prometheus_client import multiprocess
{% endif %}
workers = 2 * multiprocessing.cpu_count() + 1
bind = "0.0.0.0:8000"
wsgi_app = "{{ cookiecutter.django_project_name }}.wsgi:application"
access_logfile = "-"


{% if cookiecutter.monitoring == "y" -%}
def child_exit(server, worker):
    multiprocess.mark_process_dead(worker.pid)
{%- endif %}
