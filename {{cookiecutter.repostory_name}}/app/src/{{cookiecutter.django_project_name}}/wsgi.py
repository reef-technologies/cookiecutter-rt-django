import os

from django.core.wsgi import get_wsgi_application
{% if cookiecutter.observability %}
from {{cookiecutter.django_project_name}}.otel import instrument_before_fork
{% endif %}

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{cookiecutter.django_project_name}}.settings")

{% if cookiecutter.observability %}
instrument_before_fork()
{% endif %}

application = get_wsgi_application()
