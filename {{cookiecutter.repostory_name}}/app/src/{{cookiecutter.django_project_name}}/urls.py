from django.conf import settings
from django.contrib.admin.sites import site
from django.urls import include, path
{% if cookiecutter.use_fingerprinting == "y" -%}
from fingerprint.views import FingerprintView
{% endif -%}
{% if cookiecutter.monitoring == "y" %}
from .{{cookiecutter.django_default_app_name}}.business_metrics import metrics_manager
from .{{cookiecutter.django_default_app_name}}.metrics import metrics_view
{%- endif %}

urlpatterns = [
    path('admin/', site.urls),
    path('', include('django.contrib.auth.urls')),
    {% if cookiecutter.use_fingerprinting == "y" -%}
    path('redirect/', FingerprintView.as_view(), name='fingerprint'),
    {% endif -%}
    {%- if cookiecutter.monitoring == "y" %}
    path('metrics', metrics_view, name="prometheus-django-metrics"),
    path('business-metrics', metrics_manager.view, name="prometheus-business-metrics"),
    {%- endif %}
]

if settings.DEBUG_TOOLBAR:
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]
