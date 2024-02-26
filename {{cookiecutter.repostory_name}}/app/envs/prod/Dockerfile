{% if cookiecutter.use_alpine_linux == "y" -%}
ARG BASE_IMAGE=python:3.11-alpine
{% else -%}
ARG BASE_IMAGE=python:3.11-slim
{% endif %}

FROM $BASE_IMAGE AS base-image
LABEL builder=true

WORKDIR /root/src/

RUN pip3 install --no-cache-dir 'pdm>=2.12,<3'

COPY pyproject.toml pdm.lock ./
RUN pdm lock --check

{% if cookiecutter.use_alpine_linux == "y" -%}
RUN grep uvicorn pdm.lock && apk add --no-cache build-base || true
RUN grep psycopg pdm.lock && apk add --no-cache postgresql-dev gcc python3-dev musl-dev libffi-dev || true
RUN grep Pillow pdm.lock && apk add --no-cache jpeg-dev tiff-dev zlib-dev libwebp-dev gcc python3-dev musl-dev || true
{% endif -%}

{% if cookiecutter.use_alpine_linux == "y" -%}
RUN apk add git
{%- else -%}
RUN apt-get update && apt-get install -y git
{%- endif %}


RUN pdm config python.use_venv False && pdm sync --prod --group :all
RUN mkdir -p /opt/ && mv __pypackages__/3.11/ /opt/pypackages/
ENV PATH=/opt/pypackages/bin:$PATH
ENV PYTHONPATH=/opt/pypackages/lib:$PYTHONPATH

COPY ./app/src/ /root/src/
COPY ./app/envs/prod/entrypoint.sh /root/src/
COPY ./app/envs/prod/gunicorn.conf.py /root/src/
COPY ./app/envs/prod/celery-entrypoint.sh /root/src/
COPY ./app/envs/prod/prometheus-cleanup.sh /root/src/

RUN python3 -m compileall -b -f -q /root/
RUN ENV=prod ENV_FILL_MISSING_VALUES=1 SECRET_KEY=dummy python3 manage.py collectstatic --no-input --clear


FROM $BASE_IMAGE AS secondary-image
LABEL builder=false

{% if cookiecutter.use_alpine_linux == "y" -%}
RUN apk add wget
{%- else -%}
RUN apt-get update \
  && apt-get install -y wget \
  && rm -rf /var/lib/apt/lists/*
{%- endif %}

WORKDIR /root/src/
ENV PYTHONUNBUFFERED=1
ENV PATH=/opt/pypackages/bin:$PATH
ENV PYTHONPATH=/opt/pypackages/lib:$PYTHONPATH

COPY --from=base-image /root/src/ /root/src/
COPY --from=base-image /opt/pypackages/ /opt/pypackages/

{% if cookiecutter.use_alpine_linux == "y" -%}
RUN grep psycopg pdm.lock && apk add --no-cache libpq || true
RUN grep Pillow pdm.lock && apk add --no-cache jpeg tiff zlib libwebp || true
{%- endif %}

EXPOSE 8000

CMD ["./entrypoint.sh"]
