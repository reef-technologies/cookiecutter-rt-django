from django.apps import AppConfig
{% if cookiecutter.monitoring == "y" and cookiecutter.use_constance == "y" %}
from .constance_prometheus import export_config
{% endif %}


class {{cookiecutter.django_default_app_name|title}}Config(AppConfig):
    name = '{{cookiecutter.django_project_name}}.{{cookiecutter.django_default_app_name}}'

{% if cookiecutter.monitoring == "y" and cookiecutter.use_constance == "y" %}
    def ready(self):
        export_config()
{% endif %}
