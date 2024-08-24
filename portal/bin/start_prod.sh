#!/bin/sh

set -o errexit
set -o nounset


poetry run python manage.py migrate
poetry run gunicorn config.wsgi --bind 0.0.0.0:5000 --chdir /app --access-logfile - --capture-output --log-level debug --log-file -
