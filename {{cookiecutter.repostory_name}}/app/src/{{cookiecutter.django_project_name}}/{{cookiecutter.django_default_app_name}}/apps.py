from django.apps import AppConfig
{% if cookiecutter.monitoring == "y" and cookiecutter.use_constance == "y" %}
from .constance_prometheus import store_monitored
{% endif %}


class {{cookiecutter.django_default_app_name|title}}Config(AppConfig):
    name = '{{cookiecutter.django_project_name}}.{{cookiecutter.django_default_app_name}}'

{% if cookiecutter.monitoring == "y" and cookiecutter.use_constance == "y" %}
    def ready(self):
        store_monitored()
{% endif %}
