{%- if cookiecutter.monitoring == "y" -%}
from django_business_metrics.v0 import BusinessMetricsManager, users, active_users

metrics_manager = BusinessMetricsManager()

(metrics_manager
    .add(users)
    .add(active_users))
{% endif -%}
