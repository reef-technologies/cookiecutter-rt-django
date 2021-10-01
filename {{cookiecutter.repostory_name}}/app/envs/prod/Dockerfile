{% if cookiecutter.use_alpine_linux == "y" -%}
ARG BASE_IMAGE=python:3.9-alpine
{% else -%}
ARG BASE_IMAGE=python:3.9
{% endif %}

FROM $BASE_IMAGE AS base-image
LABEL builder=true

WORKDIR /root/src/
ENV PATH=/root/.local/bin:$PATH

RUN pip3 install --no-cache-dir -U pip
RUN pip3 install --user --no-cache-dir gunicorn==20.1.0

COPY ./src/requirements.txt requirements.txt

{% if cookiecutter.use_alpine_linux == "y" -%}
RUN grep uvicorn requirements.txt && apk add --no-cache build-base || true
RUN grep psycopg2 requirements.txt && apk add --no-cache postgresql-dev gcc python3-dev musl-dev libffi-dev || true
RUN grep Pillow requirements.txt && apk add --no-cache jpeg-dev tiff-dev zlib-dev libwebp-dev gcc python3-dev musl-dev || true
RUN grep git+ requirements.txt && apk add --no-cache git || true
{% endif -%}

RUN pip3 install --user --no-cache-dir -r requirements.txt

COPY ./src/ /root/src/
COPY ./envs/prod/entrypoint.sh /root/src/
COPY ./envs/prod/celery-entrypoint.sh /root/src/

RUN python3 -m compileall -b -f -q /root/
RUN ENV=prod ENV_FILL_MISSING_VALUES=1 SECRET_KEY=dummy python3 manage.py collectstatic --no-input --clear


FROM $BASE_IMAGE AS secondary-image
LABEL builder=false

WORKDIR /root/src/
ENV PYTHONUNBUFFERED=1
ENV PATH=/root/.local/bin:$PATH

COPY --from=base-image /root/ /root/

{% if cookiecutter.use_alpine_linux == "y" -%}
RUN apk add wget
RUN grep psycopg2 requirements.txt && apk add --no-cache libpq || true
RUN grep Pillow requirements.txt && apk add --no-cache jpeg tiff zlib libwebp || true
{% endif -%}

EXPOSE 8000

CMD ["./entrypoint.sh"]
