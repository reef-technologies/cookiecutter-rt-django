import os

{% if cookiecutter.use_channels %}
from channels.routing import ProtocolTypeRouter, URLRouter
{% endif %}
from django.core.asgi import get_asgi_application
{% if cookiecutter.observability %}
from {{cookiecutter.django_project_name}}.otel import instrument_before_fork
{% endif %}

# init django before importing urls
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "{{cookiecutter.django_project_name}}.settings")

{% if cookiecutter.observability %}
instrument_before_fork()
{% endif %}

http_app = get_asgi_application()

{% if cookiecutter.use_channels %}
from .urls import ws_urlpatterns  # noqa
{% endif %}

{% if cookiecutter.use_channels %}

application = ProtocolTypeRouter(
    {
        "http": http_app,
        "websocket": URLRouter(ws_urlpatterns),
    }
)
{% else %}
application = http_app
{% endif %}
