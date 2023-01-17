{% if cookiecutter.use_alpine_linux == "y" -%}
ARG BASE_IMAGE=python:3.9-alpine
{% else -%}
ARG BASE_IMAGE=python:3.9-slim
{% endif %}

FROM $BASE_IMAGE AS base-image
LABEL builder=true

WORKDIR /root/src/
ENV PATH=/root/.local/bin:$PATH

RUN pip3 install --no-cache-dir -U pip

COPY ./src/requirements.txt requirements.txt

{% if cookiecutter.use_alpine_linux == "y" -%}
RUN grep psycopg2 requirements.txt && apk add --no-cache postgresql-dev gcc python3-dev musl-dev libffi-dev || true
{% endif -%}

RUN pip3 install --user --no-cache-dir -r requirements.txt

COPY ./src/ /root/src/
COPY ./envs/dev/celery-entrypoint.sh /root/src/
