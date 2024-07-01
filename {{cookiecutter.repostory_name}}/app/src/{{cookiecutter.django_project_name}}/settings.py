"""
Django settings for {{cookiecutter.django_project_name}} project.
"""

import inspect
import logging
{% if cookiecutter.use_celery == "y" -%}
from datetime import timedelta
{% endif -%}
from functools import wraps

import environ

{% if cookiecutter.use_celery == "y" -%}
# from celery.schedules import crontab
{% endif -%}
import structlog

root = environ.Path(__file__) - 2

env = environ.Env(DEBUG=(bool, False))

# .env file contents are not passed to docker image during build stage;
# this results in errors if you require some env var to be set, as if in "env('MYVAR')" -
# obviously it's not set during build stage, but you don't care and want to ignore that.
# To mitigate this, we set ENV_FILL_MISSING_VALUES=1 during build phase, and it activates
# monkey-patching of "environ" module, so that all unset variables get some default value
# and the library does not complain anymore
if env.bool("ENV_FILL_MISSING_VALUES", default=False):

    def patch(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if kwargs.get("default") is env.NOTSET:
                kwargs["default"] = {
                    bool: False,
                    int: 0,
                    float: 0.0,
                }.get(kwargs.get("cast"), None)

            return fn(*args, **kwargs)

        return wrapped

    for name, method in inspect.getmembers(env, predicate=inspect.ismethod):
        setattr(env, name, patch(method))

# read from the .env file if hasn't been sourced already
if env("ENV", default=None) is None:
    env.read_env(root("../../.env"))

ENV = env("ENV")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env("DEBUG")

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    {%- if cookiecutter.use_channels == "y" %}
    "daphne",
    {%- endif %}
    {%- if cookiecutter.monitoring == "y" %}
    "django_prometheus",
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.storage",
    "health_check.contrib.migrations",
    "health_check.contrib.psutil",
    "health_check.contrib.redis",
    {%- endif %}
    {%- if cookiecutter.monitoring == "y" and cookiecutter.use_celery == "y" %}
    "health_check.contrib.celery",
    "health_check.contrib.celery_ping",
    {%- endif %}
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_extensions",
    "django_probes",
    "django_structlog",
    "constance",
    {% if cookiecutter.use_fingerprinting == "y" -%}
    "fingerprint",
    {% endif -%}
    "{{cookiecutter.django_project_name}}.{{cookiecutter.django_default_app_name}}",
]

{%- if cookiecutter.monitoring == "y" %}
PROMETHEUS_EXPORT_MIGRATIONS = True
{%- endif %}
{%- if cookiecutter.monitor_view_execution_time_in_djagno == "y" and cookiecutter.monitoring == "y" %}
PROMETHEUS_LATENCY_BUCKETS = (
    0.008,
    0.016,
    0.032,
    0.062,
    0.125,
    0.25,
    0.5,
    1.0,
    2.0,
    4.0,
    8.0,
    16.0,
    32.0,
    64.0,
    float("inf"),
){%- endif %}


MIDDLEWARE = [
    {%- if cookiecutter.monitor_view_execution_time_in_djagno == "y" and cookiecutter.monitoring == "y" %}
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    {%- endif %}
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    {%- if cookiecutter.monitor_view_execution_time_in_djagno == "y" and cookiecutter.monitoring == "y" %}
    "django_prometheus.middleware.PrometheusAfterMiddleware",
    {%- endif %}
    "django_structlog.middlewares.RequestMiddleware",
]


if DEBUG_TOOLBAR := env.bool("DEBUG_TOOLBAR", default=False):
    INTERNAL_IPS = [
        "127.0.0.1",
    ]

    DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda _request: True}
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE = ["debug_toolbar.middleware.DebugToolbarMiddleware"] + MIDDLEWARE

if CORS_ENABLED := env.bool("CORS_ENABLED", default=True):
    INSTALLED_APPS.append("corsheaders")
    MIDDLEWARE = ["corsheaders.middleware.CorsMiddleware"] + MIDDLEWARE
    CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
    CORS_ALLOWED_ORIGIN_REGEXES = env.list("CORS_ALLOWED_ORIGIN_REGEXES", default=[])
    CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=False)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Content Security Policy
if CSP_ENABLED := env.bool("CSP_ENABLED"):
    MIDDLEWARE.append("csp.middleware.CSPMiddleware")

    CSP_REPORT_ONLY = env.bool("CSP_REPORT_ONLY", default=True)
    CSP_REPORT_URL = env("CSP_REPORT_URL", default=None) or None

    CSP_DEFAULT_SRC = env.tuple("CSP_DEFAULT_SRC")
    CSP_SCRIPT_SRC = env.tuple("CSP_SCRIPT_SRC")
    CSP_STYLE_SRC = env.tuple("CSP_STYLE_SRC")
    CSP_FONT_SRC = env.tuple("CSP_FONT_SRC")
    CSP_IMG_SRC = env.tuple("CSP_IMG_SRC")
    CSP_MEDIA_SRC = env.tuple("CSP_MEDIA_SRC")
    CSP_OBJECT_SRC = env.tuple("CSP_OBJECT_SRC")
    CSP_FRAME_SRC = env.tuple("CSP_FRAME_SRC")
    CSP_CONNECT_SRC = env.tuple("CSP_CONNECT_SRC")
    CSP_CHILD_SRC = env.tuple("CSP_CHILD_SRC")
    CSP_MANIFEST_SRC = env.tuple("CSP_MANIFEST_SRC")
    CSP_WORKER_SRC = env.tuple("CSP_WORKER_SRC")

    CSP_BLOCK_ALL_MIXED_CONTENT = env.bool("CSP_BLOCK_ALL_MIXED_CONTENT", default=False)
    CSP_EXCLUDE_URL_PREFIXES = env.tuple("CSP_EXCLUDE_URL_PREFIXES", default=tuple())


ROOT_URLCONF = "{{cookiecutter.django_project_name}}.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [root("{{cookiecutter.django_project_name}}/templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "{{cookiecutter.django_project_name}}.wsgi.application"
{%- if cookiecutter.use_channels == "y" %}
ASGI_APPLICATION = "{{cookiecutter.django_project_name}}.asgi.application"
{%- endif %}

DATABASES = {}
if env("DATABASE_POOL_URL"):  # DB transaction-based connection pool, such as one provided PgBouncer
    DATABASES["default"] = {
        **env.db_url("DATABASE_POOL_URL"),
        "DISABLE_SERVER_SIDE_CURSORS": True,  # prevents random cursor errors with transaction-based connection pool
    }
elif env("DATABASE_URL"):
    DATABASES["default"] = env.db_url("DATABASE_URL")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = env("STATIC_URL", default="/static/")
STATIC_ROOT = env("STATIC_ROOT", default=root("static"))
MEDIA_URL = env("MEDIA_URL", default="/media/")
MEDIA_ROOT = env("MEDIA_ROOT", default=root("media"))

# Security
# redirect HTTP to HTTPS
if env.bool("HTTPS_REDIRECT", default=False) and not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_REDIRECT_EXEMPT = []  # type: ignore
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
else:
    SECURE_SSL_REDIRECT = False

{%- if cookiecutter.use_channels == "y" %}
CHANNELS_BACKEND_URL = env("CHANNELS_BACKEND_URL")
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [{"address": CHANNELS_BACKEND_URL}],
        },
    },
}
{%- endif %}

{%- if cookiecutter.monitoring == "y" %}
REDIS_HOST = env("REDIS_HOST")
REDIS_PORT = env.int("REDIS_PORT")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"
{%- endif %}

{%- if cookiecutter.use_celery == "y" %}

CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
CONSTANCE_CONFIG = {
    # "PARAMETER": (default-value, "Help text", type),
}


CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="")
CELERY_RESULT_BACKEND = env("CELERY_BROKER_URL", default="")  # store results in Redis
CELERY_RESULT_EXPIRES = int(timedelta(days=1).total_seconds())  # time until task result deletion
CELERY_COMPRESSION = "gzip"  # task compression
CELERY_MESSAGE_COMPRESSION = "gzip"  # result compression
CELERY_SEND_EVENTS = True  # needed for worker monitoring
CELERY_BEAT_SCHEDULE = {  # type: ignore
    # 'task_name': {
    #     'task': "{{cookiecutter.django_project_name}}.{{cookiecutter.django_default_app_name}}.tasks.demo_task",
    #     'args': [2, 2],
    #     'kwargs': {},
    #     'schedule': crontab(minute=0, hour=0),
    #     'options': {"time_limit": 300},
    # },
}
CELERY_TASK_ROUTES = ["{{cookiecutter.django_project_name}}.celery.route_task"]
CELERY_TASK_TIME_LIMIT = int(timedelta(minutes=5).total_seconds())
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_WORKER_PREFETCH_MULTIPLIER = env.int("CELERY_WORKER_PREFETCH_MULTIPLIER", default=10)
CELERY_BROKER_POOL_LIMIT = env.int("CELERY_BROKER_POOL_LIMIT", default=50)
{%- endif %}

EMAIL_BACKEND = env("EMAIL_BACKEND")
EMAIL_FILE_PATH = env("EMAIL_FILE_PATH")
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env.int("EMAIL_PORT")
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "main": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "main",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "django_structlog.*": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "celery": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "celery.task": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "celery.redirected": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "psycopg.pq": {
            # only logs unavailable libs during psycopg initialization
            "propagate": False,
        },
    },
}
DJANGO_STRUCTLOG_CELERY_ENABLED = True


def configure_structlog():
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


configure_structlog()

# Sentry
if SENTRY_DSN := env("SENTRY_DSN", default=""):
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration, ignore_logger
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(  # type: ignore
        dsn=SENTRY_DSN,
        environment=ENV,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
            RedisIntegration(),
            LoggingIntegration(
                level=logging.INFO,  # Capture info and above as breadcrumbs
                event_level=logging.ERROR,  # Send error events from log messages
            ),
        ],
    )
    ignore_logger("django.security.DisallowedHost")
