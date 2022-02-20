"""
Django settings for {{cookiecutter.django_project_name}} project.
"""

from datetime import timedelta
import logging
from functools import wraps
import inspect

import environ
{% if cookiecutter.use_celery == "y" %}
from celery.schedules import crontab
{% endif %}


root = environ.Path(__file__) - 2

env = environ.Env()

# .env file contents are not passed to docker image during build stage;
# this results in errors if you require some env var to be set, as if in "env('MYVAR')" -
# obviously it's not set during build stage, but you don't care and want to ignore that.
# To mitigate this, we set ENV_FILL_MISSING_VALUES=1 during build phase, and it activates
# monkey-patching of "environ" module, so that all unset variables are set to None and
# the library is not complaining anymore
if env.bool('ENV_FILL_MISSING_VALUES', default=False):

    def patch(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if kwargs.get('default') is env.NOTSET:
                kwargs['default'] = None
            return fn(*args, **kwargs)
        return wrapped

    for name, method in inspect.getmembers(env, predicate=inspect.ismethod):
        setattr(env, name, patch(method))

# read from the .env file if hasn't been sourced already
if env('ENV', default=None) is None:
    env.read_env(root('../../.env'))

ENV = env('ENV')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG')

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'django_extensions',
    'django_probes',

    '{{cookiecutter.django_project_name}}.{{cookiecutter.django_default_app_name}}',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if DEBUG_TOOLBAR := env.bool('DEBUG_TOOLBAR'):
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda _request: True
    }
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE

if CORS_ENABLED := env.bool('CORS_ENABLED'):
    INSTALLED_APPS.append('corsheaders')
    MIDDLEWARE = ['corsheaders.middleware.CorsMiddleware'] + MIDDLEWARE
    CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS')
    CORS_ALLOWED_ORIGIN_REGEXES = env.list('CORS_ALLOWED_ORIGIN_REGEXES')
    CORS_ALLOW_ALL_ORIGINS = env.bool('CORS_ALLOW_ALL_ORIGINS')

# Content Security Policy
if CSP_ENABLED := env.bool('CSP_ENABLED'):
    MIDDLEWARE.append('csp.middleware.CSPMiddleware')

    CSP_REPORT_ONLY = env.bool('CSP_REPORT_ONLY')
    CSP_REPORT_URL = env('CSP_REPORT_URL') or None

    CSP_DEFAULT_SRC = env.tuple('CSP_DEFAULT_SRC')
    CSP_SCRIPT_SRC = env.tuple('CSP_SCRIPT_SRC')
    CSP_STYLE_SRC = env.tuple('CSP_STYLE_SRC')
    CSP_FONT_SRC = env.tuple('CSP_FONT_SRC')
    CSP_IMG_SRC = env.tuple('CSP_IMG_SRC')
    CSP_MEDIA_SRC = env.tuple('CSP_MEDIA_SRC')
    CSP_OBJECT_SRC = env.tuple('CSP_OBJECT_SRC')
    CSP_FRAME_SRC = env.tuple('CSP_FRAME_SRC')
    CSP_CONNECT_SRC = env.tuple('CSP_CONNECT_SRC')
    CSP_CHILD_SRC = env.tuple('CSP_CHILD_SRC')
    CSP_MANIFEST_SRC = env.tuple('CSP_MANIFEST_SRC')
    CSP_WORKER_SRC = env.tuple('CSP_WORKER_SRC')

    CSP_BLOCK_ALL_MIXED_CONTENT = env.bool('CSP_BLOCK_ALL_MIXED_CONTENT')
    CSP_EXCLUDE_URL_PREFIXES = env.tuple('CSP_EXCLUDE_URL_PREFIXES')


ROOT_URLCONF = '{{cookiecutter.django_project_name}}.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [root('{{cookiecutter.django_project_name}}/templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = '{{cookiecutter.django_project_name}}.wsgi.application'


if env('DATABASE_URL'):
    DATABASES = {
        'default': env.db(),
    }
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = env('STATIC_URL')
STATIC_ROOT = env('STATIC_ROOT')
MEDIA_URL = env('MEDIA_URL')
MEDIA_ROOT = env('MEDIA_ROOT')

# Redirect HTTP to HTTPS
if env.bool('HTTPS_REDIRECT') and not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_REDIRECT_EXEMPT = []
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
else:
    SECURE_SSL_REDIRECT = False

{% if cookiecutter.use_celery == "y" %}
CELERY_BROKER_URL = env('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = env('CELERY_BROKER_URL')  # store results in Redis
CELERY_RESULT_EXPIRES = int(timedelta(days=1).total_seconds())  # time until task result deletion
CELERY_COMPRESSION = 'gzip'  # task compression
CELERY_MESSAGE_COMPRESSION = 'gzip'  # result compression
CELERY_SEND_EVENTS = True  # needed for worker monitoring
CELERY_BEAT_SCHEDULE = {
    # 'task_name': {
    #     'task': '{{cookiecutter.django_project_name}}.{{cookiecutter.django_default_app_name}}.tasks.demo_task',
    #     'args': [2, 2],
    #     'kwargs': {},
    #     'schedule': crontab(minute=0, hour=0),
    #     'options': {'time_limit': 300},
    # },
}
CELERY_TASK_ROUTES = ['{{cookiecutter.django_project_name}}.celery.route_task']
CELERY_TASK_TIME_LIMIT = int(timedelta(minutes=5).total_seconds())
CELERY_TASK_ALWAYS_EAGER = env.bool('CELERY_TASK_ALWAYS_EAGER')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_WORKER_PREFETCH_MULTIPLIER = env.int('CELERY_WORKER_PREFETCH_MULTIPLIER')
CELERY_BROKER_POOL_LIMIT = env.int('CELERY_BROKER_POOL_LIMIT')
{% endif %}

EMAIL_BACKEND = env('EMAIL_BACKEND')
EMAIL_FILE_PATH = env('EMAIL_FILE_PATH')
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env.int('EMAIL_PORT')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'main': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'main',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Sentry
if SENTRY_DSN := env('SENTRY_DSN'):
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    sentry_sdk.init(
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
