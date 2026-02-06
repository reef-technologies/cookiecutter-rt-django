{% if cookiecutter.use_alpine_linux == "y" %}
ARG BASE_IMAGE=python:3.11-alpine
{% else %}
ARG BASE_IMAGE=python:3.11-slim
{% endif %}

FROM $BASE_IMAGE AS base-image
LABEL builder=true

COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/

WORKDIR /root/src/

COPY pyproject.toml uv.lock ./

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

{% if cookiecutter.use_alpine_linux == "y" %}
RUN grep uvicorn uv.lock && apk add --no-cache build-base || true
RUN grep psycopg uv.lock && apk add --no-cache postgresql-dev gcc python3-dev musl-dev libffi-dev || true
RUN grep Pillow uv.lock && apk add --no-cache jpeg-dev tiff-dev zlib-dev libwebp-dev gcc python3-dev musl-dev || true
{% endif %}

{% if cookiecutter.use_alpine_linux == "y" %}
RUN apk add git
{% else %}
RUN apt-get update && apt-get install -y git
{% endif %}

RUN --mount=type=cache,target=/root/.cache/uv \
	uv sync --frozen --no-install-project --no-dev --no-editable

COPY ./app/src/ ./app/envs/prod/entrypoint.sh ./app/envs/prod/gunicorn.conf.py ./app/envs/prod/celery-entrypoint.sh ./app/envs/prod/prometheus-cleanup.sh /root/src/

RUN --mount=type=cache,target=/root/.cache/uv \
	uv sync --frozen --no-dev --no-editable

RUN ENV=prod ENV_FILL_MISSING_VALUES=1 SECRET_KEY=dummy uv run python3 manage.py collectstatic --no-input --clear


FROM $BASE_IMAGE AS secondary-image
LABEL builder=false

{% if cookiecutter.use_alpine_linux == "y" %}
RUN apk add wget
{% else %}
RUN apt-get update \
	&& apt-get install -y wget \
	&& rm -rf /var/lib/apt/lists/*
{% endif %}

WORKDIR /root/src/
ENV PYTHONUNBUFFERED=1
ENV PATH="/root/src/.venv/bin:$PATH"

COPY --from=base-image /root/src/ /root/src/

{% if cookiecutter.use_alpine_linux == "y" %}
RUN grep psycopg uv.lock && apk add --no-cache libpq || true
RUN grep Pillow uv.lock && apk add --no-cache jpeg tiff zlib libwebp || true
{% endif %}

{% if cookiecutter.monitoring == "y" %}
ENV PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus-metrics
RUN mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
{% endif %}

CMD ["./entrypoint.sh"]
