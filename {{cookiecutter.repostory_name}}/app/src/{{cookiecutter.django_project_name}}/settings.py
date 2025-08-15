"""
Django settings for {{cookiecutter.django_project_name}} project.
"""

import inspect
import logging
{% if cookiecutter.use_celery == "y" %}
from datetime import timedelta
{% endif %}
from functools import wraps

import environ
import structlog

{% if cookiecutter.use_celery == "y" %}
# from celery.schedules import crontab
from kombu import Queue
{% endif %}
{% if cookiecutter.use_allauth == "y" %}
from django.urls import reverse_lazy
{% endif %}

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

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    {% if cookiecutter.use_allauth == "y" %}
    "allauth.account.auth_backends.AuthenticationBackend",
    {% endif %}
]

INSTALLED_APPS = [
    {% if cookiecutter.use_channels == "y" %}
    "daphne",
    {% endif %}
    {% if cookiecutter.monitoring == "y" %}
    "django_prometheus",
    "health_check",
    "health_check.db",
    "health_check.cache",
    "health_check.storage",
    "health_check.contrib.migrations",
    "health_check.contrib.psutil",
    "health_check.contrib.redis",
    {% endif %}
    {% if cookiecutter.monitoring == "y" and cookiecutter.use_celery == "y" %}
    "health_check.contrib.celery",
    "health_check.contrib.celery_ping",
    {% endif %}
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
    {% if cookiecutter.use_fingerprinting == "y" %}
    "fingerprint",
    {% endif %}
    {% if cookiecutter.use_allauth == "y" %}
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    {% if 'apple' in cookiecutter.allauth_providers %}
    "allauth.socialaccount.providers.apple",
    {% endif %}
    {% if 'atlassian' in cookiecutter.allauth_providers %}
    "allauth.socialaccount.providers.atlassian",
    {% endif %}
    {% if 'discord' in cookiecutter.allauth_providers %}
    "allauth.socialaccount.providers.discord",
    {% endif %}
    {% if 'facebook' in cookiecutter.allauth_providers %}
    "allauth.socialaccount.providers.facebook",
    {% endif %}
    {% if 'github' in cookiecutter.allauth_providers %}
    "allauth.socialaccount.providers.github",
    {% endif %}
    {% if 'gitlab' in cookiecutter.allauth_providers %}
    "allauth.socialaccount.providers.gitlab",
    {% endif %}
    {% if 'google' in cookiecutter.allauth_providers %}
    "allauth.socialaccount.providers.google",
    {% endif %}
    {% if 'microsoft' in cookiecutter.allauth_providers %}
    "allauth.socialaccount.providers.microsoft",
    {% endif %}
    {% if 'openid_connect' in cookiecutter.allauth_providers %}
    "allauth.socialaccount.providers.openid_connect",
    {% endif %}
    {% if 'twitter' in cookiecutter.allauth_providers %}
    "allauth.socialaccount.providers.twitter_oauth2",
    {% endif %}
    {% endif %}
    {% if cookiecutter.use_rest_framework == "y" %}
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    {% endif %}
    "{{cookiecutter.django_project_name}}.{{cookiecutter.django_default_app_name}}",
]

{% if cookiecutter.monitoring == "y" %}
PROMETHEUS_EXPORT_MIGRATIONS = env.bool("PROMETHEUS_EXPORT_MIGRATIONS", default=True)
{% if cookiecutter.monitor_view_execution_time_in_djagno == "y" %}
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
)
{% endif %}
{% endif %}

MIDDLEWARE = [
    {% if cookiecutter.monitor_view_execution_time_in_djagno == "y" and cookiecutter.monitoring == "y" %}
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    {% endif %}
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    {% if cookiecutter.monitor_view_execution_time_in_djagno == "y" and cookiecutter.monitoring == "y" %}
    "django_prometheus.middleware.PrometheusAfterMiddleware",
    {% endif %}
    "django_structlog.middlewares.RequestMiddleware",
    {% if cookiecutter.use_allauth == "y" %}
    "allauth.account.middleware.AccountMiddleware",
    {% endif %}
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
{% if cookiecutter.use_channels == "y" %}
ASGI_APPLICATION = "{{cookiecutter.django_project_name}}.asgi.application"
{% endif %}

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

{% if cookiecutter.use_rest_framework == "y" %}
REST_FRAMEWORK = {
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.BasicAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAdminUser",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "10/m", "user": "100/m"},
    "DEFAULT_PAGINATION_CLASS": "{{cookiecutter.django_project_name}}.api.pagination.CursorPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}
SPECTACULAR_SETTINGS = {
    "SERVE_PERMISSIONS": [
        "rest_framework.permissions.IsAdminUser",
    ],
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
}
{% endif %}

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

{% if cookiecutter.use_channels == "y" %}
CHANNELS_BACKEND_URL = env("CHANNELS_BACKEND_URL")
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [{"address": CHANNELS_BACKEND_URL}],
        },
    },
}
{% endif %}

{% if cookiecutter.monitoring == "y" %}
REDIS_HOST = env("REDIS_HOST")
REDIS_PORT = env.int("REDIS_PORT")
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}"
{% endif %}

CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
CONSTANCE_CONFIG = {
    # "PARAMETER": (default-value, "Help text", type),
}

{% if cookiecutter.use_celery == "y" %}
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
CELERY_TASK_CREATE_MISSING_QUEUES = False
CELERY_TASK_QUEUES = (Queue("celery"), Queue("worker"), Queue("dead_letter"))
CELERY_TASK_DEFAULT_EXCHANGE = "celery"
CELERY_TASK_DEFAULT_ROUTING_KEY = "celery"
CELERY_TASK_ANNOTATIONS = {"*": {"acks_late": True, "reject_on_worker_lost": True}}
CELERY_TASK_ROUTES = {"*": {"queue": "celery"}}
CELERY_TASK_TIME_LIMIT = int(timedelta(minutes=5).total_seconds())
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_WORKER_SEND_TASK_EVENTS = True
CELERY_TASK_SEND_SENT_EVENT = True
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_WORKER_PREFETCH_MULTIPLIER = env.int("CELERY_WORKER_PREFETCH_MULTIPLIER", default=1)
CELERY_BROKER_POOL_LIMIT = env.int("CELERY_BROKER_POOL_LIMIT", default=50)

DJANGO_STRUCTLOG_CELERY_ENABLED = True
{% endif %}

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
        # Fix spamming DEBUG-level logs in manage.py shell and shell_plus.
        "parso": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}


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
    {% if cookiecutter.use_celery == "y" %}
    from sentry_sdk.integrations.celery import CeleryIntegration
    {% endif %}
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration, ignore_logger
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(  # type: ignore
        dsn=SENTRY_DSN,
        environment=ENV,
        integrations=[
            DjangoIntegration(),
            {% if cookiecutter.use_celery == "y" %}
            CeleryIntegration(),
            {% endif %}
            RedisIntegration(),
            LoggingIntegration(
                level=logging.INFO,  # Capture info and above as breadcrumbs
                event_level=logging.ERROR,  # Send error events from log messages
            ),
        ],
    )
    ignore_logger("django.security.DisallowedHost")

{% if cookiecutter.use_allauth == "y" %}
LOGIN_URL = reverse_lazy("account_login")
LOGIN_REDIRECT_URL = "/"
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_UNKNOWN_ACCOUNTS = False
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_CHANGE_EMAIL = False
ACCOUNT_MAX_EMAIL_ADDRESSES = 1
SOCIALACCOUNT_PROVIDERS = {
    {% if 'apple' in cookiecutter.allauth_providers %}
    "apple": {
        "APP": {
            "client_id": env("APPLE_LOGIN_CLIENT_ID"),
            "secret": env("APPLE_LOGIN_SECRET"),
            "key": env("APPLE_LOGIN_KEY"),
            "settings": {
                "certificate_key": env("APPLE_LOGIN_CERTIFICATE_PRIVATE_KEY"),
            },
        },
        {% if cookiecutter.allauth_trust_external_emails == "y" %}
        # Trust, that Apple verifies that the users own the addresses that we get from the SSO flow.
        # This allows users to log in to any existing account with any configured provider if the email addresses match.
        "EMAIL_AUTHENTICATION": True,
        {% endif %}
    },
    {% endif %}
    {% if 'microsoft' in cookiecutter.allauth_providers %}
    "microsoft": {
        "APP": {
            "client_id": env("MICROSOFT_LOGIN_CLIENT_ID"),
            "secret": env("MICROSOFT_LOGIN_SECRET"),
            "settings": {
                "tenant": "organizations",
            },
        },
        {% if cookiecutter.allauth_trust_external_emails == "y" %}
        # Trust, that Microsoft verifies that the users own the addresses that we get from the SSO flow.
        # This allows users to log in to any existing account with any configured provider if the email addresses match.
        "EMAIL_AUTHENTICATION": True,
        {% endif %}
    },
    {% endif %}
    {% if 'openid_connect' in cookiecutter.allauth_providers %}
    "openid_connect": {
        "APP": {
            "client_id": "oidc",
            "name": env("OPENID_CONNECT_NICE_NAME"),
            "secret": env("OPENID_CONNECT_LOGIN_SECRET"),
            "settings": {
                "server_url": env("OPENID_CONNECT_SERVER_URL")
            },
        },
        {% if cookiecutter.allauth_trust_external_emails == "y" %}
        # Trust, that this provider verifies that the users own the addresses that we get from the SSO flow.
        # This allows users to log in to any existing account with any configured provider if the email addresses match.
        "EMAIL_AUTHENTICATION": True,
        {% endif %}
    },
    {% endif %}
    {% for provider in ['atlassian', 'discord', 'facebook', 'github', 'gitlab', 'google', 'twitter'] if provider in cookiecutter.allauth_providers %}
    "{{ provider }}": {
        "APP": {
            "client_id": env("{{ provider | upper }}_LOGIN_CLIENT_ID"),
            "secret": env("{{ provider | upper }}_LOGIN_SECRET"),
        },
        {% if cookiecutter.allauth_trust_external_emails == "y" %}
        # Trust, that {{ provider | capitalize }} verifies that the users own the addresses that we get from the SSO flow.
        # This allows users to log in to any existing account with any configured provider if the email addresses match.
        "EMAIL_AUTHENTICATION": True,
        {% endif %}
    },
    {% endfor %}
}
{% endif %}