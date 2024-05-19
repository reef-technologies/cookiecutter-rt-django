from django.conf import settings
from django.contrib.admin.sites import site
from django.urls import include, path
{% if cookiecutter.use_fingerprinting == "y" -%}
from fingerprint.views import FingerprintView
{% endif -%}
{% if cookiecutter.monitoring == "y" %}
from .{{cookiecutter.django_default_app_name}}.business_metrics import metrics_manager
{%- endif %}
{%- if cookiecutter.use_channels == "y" %}
from .{{cookiecutter.django_default_app_name}}.consumers import DefaultConsumer
{%- endif %}
{%- if cookiecutter.monitoring == "y" %}
from .{{cookiecutter.django_default_app_name}}.metrics import metrics_view
{%- endif %}

urlpatterns = [
    path("admin/", site.urls),
    path("", include("django.contrib.auth.urls")),
    {%- if cookiecutter.use_fingerprinting == "y" %}
    path("redirect/", FingerprintView.as_view(), name="fingerprint"),
    {%- endif %}
    {%- if cookiecutter.monitoring == "y" %}
    path("metrics", metrics_view, name="prometheus-django-metrics"),
    path("business-metrics", metrics_manager.view, name="prometheus-business-metrics"),
    path("healthcheck/", include("health_check.urls")),
    {%- endif %}
    {%- if cookiecutter.use_allauth == "y" %}
    path('accounts/', include('allauth.urls')),
    {%- endif %}
]

{%- if cookiecutter.use_channels == "y" %}
ws_urlpatterns = [
    path("ws/v0/", DefaultConsumer.as_asgi()),
]
{%- endif %}

if settings.DEBUG_TOOLBAR:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
