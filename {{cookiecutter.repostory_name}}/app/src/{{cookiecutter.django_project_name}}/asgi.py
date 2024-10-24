import os

{% if cookiecutter.use_channels == "y" -%}
from channels.routing import ProtocolTypeRouter, URLRouter
{% endif -%}
from django.core.asgi import get_asgi_application

# init django before importing urls
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{cookiecutter.django_project_name}}.settings")
http_app = get_asgi_application()

{% if cookiecutter.use_channels == "y" -%}
from .urls import ws_urlpatterns  # noqa
{%- endif %}

{%- if cookiecutter.use_channels == "y" %}

application = ProtocolTypeRouter(
    {
        "http": http_app,
        "websocket": URLRouter(ws_urlpatterns),
    }
)
{%- else %}
application = http_app
{%- endif %}
