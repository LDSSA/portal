#!/bin/sh
set -eu
poetry run python manage.py migrate --check
exec poetry run python manage.py run-edition-resets
