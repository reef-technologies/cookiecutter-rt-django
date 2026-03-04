#!/bin/bash
set -eux
find . -type d -empty -delete
uvx ruff format .
uvx ruff check --fix .
