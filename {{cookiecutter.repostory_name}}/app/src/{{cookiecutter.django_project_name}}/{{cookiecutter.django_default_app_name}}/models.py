{%- if cookiecutter.monitoring == "y" -%}
from django.db import models  # noqa


class HealthcheckModel(models.Model):
    check_date = models.DateTimeField()

    class Meta:
        db_table = "healthcheck_model"
{% endif -%}
