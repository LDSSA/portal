#!/bin/sh

set -o errexit
set -o nounset


poetry run python manage.py run-simulator
