#!/bin/sh

set -o errexit
set -o nounset


poetry run python manage.py migrate
poetry run python manage.py run-scheduler
poetry run python manage.py runserver_plus 0.0.0.0:8000

