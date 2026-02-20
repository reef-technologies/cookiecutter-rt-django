from django.conf import settings
from django.contrib.admin.sites import site
from django.http import HttpResponse
from django.urls import include, path{% if cookiecutter.use_rest_framework %}, re_path{% endif %}

{% if cookiecutter.use_rest_framework %}
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
{% endif %}
{% if cookiecutter.use_fingerprinting %}
from fingerprint.views import FingerprintView
{% endif %}

{% if cookiecutter.use_rest_framework %}
from .api.routers import router as api_router
{% endif %}
{% if cookiecutter.monitoring %}
from .{{cookiecutter.django_default_app_name}}.business_metrics import metrics_manager
{% endif %}
{% if cookiecutter.use_channels %}
from .{{cookiecutter.django_default_app_name}}.consumers import DefaultConsumer
{% endif %}
{% if cookiecutter.monitoring %}
from .{{cookiecutter.django_default_app_name}}.metrics import metrics_view

{% endif %}
urlpatterns = [
    path("alive/", lambda _: HttpResponse(b"ok")),
    path("admin/", site.urls),
    {% if cookiecutter.use_rest_framework %}
    re_path(r"^api/(?P<version>v0)/", include(api_router.urls)),
    re_path(r"^api/(?P<version>v0)/schema/$", SpectacularAPIView.as_view(), name="schema"),
    re_path(r"^api/(?P<version>v0)/schema/swagger-ui/$", SpectacularSwaggerView.as_view(url_name='schema')),
    re_path(r"^api/auth/", include("rest_framework.urls", namespace="rest_framework")),
    {% endif %}
    {% if cookiecutter.use_fingerprinting %}
    path("redirect/", FingerprintView.as_view(), name="fingerprint"),
    {% endif %}
    {% if cookiecutter.monitoring %}
    path("metrics", metrics_view, name="prometheus-django-metrics"),
    path("business-metrics", metrics_manager.view, name="prometheus-business-metrics"),
    {% endif %}
    {% if cookiecutter.use_allauth %}
    path("accounts/", include("allauth.urls")),
    {% else %}
    path("", include("django.contrib.auth.urls")),
    {% endif %}
]

{% if cookiecutter.use_channels %}
ws_urlpatterns = [
    path("ws/v0/", DefaultConsumer.as_asgi()),
]
{% endif %}

if settings.DEBUG_TOOLBAR:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]
