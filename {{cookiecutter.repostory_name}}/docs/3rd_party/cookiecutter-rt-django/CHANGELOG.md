# cookiecutter-rt-django Changelog

Main purpose of this file is to provide a changelog for the template itself.
It is not intended to be used as a changelog for the generated project.

This changelog will document any know **BREAKING** changes between versions of the template.
Please review this new entries carefully after applying `cruft update` before committing the changes.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

Currently, `cookiecutter-rt-django` has no explicit versioning amd we purely rely on `cruft` diff.

## [Unreleased]

* **BREAKING** Switched from `pdm` to [`uv`](https://docs.astral.sh/uv/) for Python dependency management.
* **BREAKING** Switched from `docker-compose` v1 script to `docker compose` v2 plugin (https://docs.docker.com/compose/cli-command/)
* **BREAKING** Added formatting with ruff.
* **BREAKING** Started using [pdm](https://github.com/pdm-project/pdm) for managing Python dependencies.
* **BREAKING** root of repository is used as docker build context instead of just `./app/`.
* **BREAKING** Updated django-environ from 0.4.5 to 0.10 (https://django-environ.readthedocs.io/en/latest/changelog.html)
* **BREAKING** Updated redis python package from 3.5.3 to 4.6 (breaking changes listed in https://github.com/redis/redis-py/releases/tag/v4.0.0b1)
* **BREAKING** Updated Python from 3.9 to 3.11
* **BREAKING** Updated Django from 3.2 to 4.2 (https://docs.djangoproject.com/en/4.2/releases/4.0/#backwards-incompatible-changes-in-4-0)
* **BREAKING** Updated django-cors-headers from 3.7 to 4.0 (https://github.com/adamchainz/django-cors-headers/blob/main/CHANGELOG.rst#400-2023-05-12)
* **BREAKING** Updated django-environ from 0.7 to 0.10 (https://django-environ.readthedocs.io/en/latest/changelog.html)
* **BREAKING** Updated Python from 3.11 to 3.14
* **BREAKING** Updated Django from 4.2 to 5.2 (https://docs.djangoproject.com/en/5.2/releases/5.0/#backwards-incompatible-changes-in-5-0)
* **BREAKING** Updated `cruft.json` variables to boolean types, so `"n"` values are treated as `True` -> when doing cruft update, make sure to update `"n"` variables to `false`, like this:

```sh
cruft update --variables-to-update '{ "use_fingerprinting": false, "use_channels": false, "csp_enabled": false, "nginx_compression_enabled": false, "nginx_tls_early_data_enabled": false, "aws_use_packer": false }'
```
* **BREAKING** Updating to 3.14 causes prometheus files to corrupt and trigger an error:
```
app-1  |   File "/root/src/.venv/lib/python3.14/site-packages/prometheus_client/mmap_dict.py", line 40, in _read_all_values
app-1  |     raise RuntimeError('Read beyond file size detected, file is corrupted.')
```
A simple solution is to stop all containers, remove prometheus data, and start the containers again:
```sh
docker compose stop
rm -rf prometheus-metrics/*
docker compose up -d
```