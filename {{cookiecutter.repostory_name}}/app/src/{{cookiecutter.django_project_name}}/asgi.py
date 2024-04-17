import os

{% if cookiecutter.use_channels == "y" -%}
from channels.routing import ProtocolTypeRouter, URLRouter
{%- endif %}
from django.core.asgi import get_asgi_application

{% if cookiecutter.use_channels == "y" -%}
from .urls import ws_urlpatterns
{%- endif %}

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{cookiecutter.django_project_name}}.settings")

{%- if cookiecutter.use_channels == "y" %}
application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": URLRouter(ws_urlpatterns),
    }
)
{%- else %}
application = get_asgi_application()
{%- endif %}
