FROM python:3.7-slim-buster

ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y \
      build-essential \
      gcc \
      python3-dev \
      libpq-dev \
      postgresql-client \
      docker

# Requirements are installed here to ensure they will be cached.
COPY ./requirements /requirements
RUN pip install -U pip
RUN pip install -r /requirements/local.txt

COPY ./docker/production/django/entrypoint /entrypoint
RUN sed -i 's/\r//' /entrypoint
RUN chmod +x /entrypoint

COPY ./docker/local/django/start /start
RUN sed -i 's/\r//' /start
RUN chmod +x /start

WORKDIR /app

ENTRYPOINT ["/entrypoint"]
