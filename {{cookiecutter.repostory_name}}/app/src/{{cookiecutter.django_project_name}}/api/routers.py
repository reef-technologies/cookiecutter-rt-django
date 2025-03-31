{% if cookiecutter.use_rest_framework == "y" -%}
from rest_framework.routers import DefaultRouter

# from .views import SomeModelViewSet

router = DefaultRouter()
# router.register(r"some", SomeModelViewSet)
{%- endif %}
