FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y \
      build-essential \
      gcc \
      python3-dev \
      libpq-dev \
      postgresql-client \
      docker \
      curl \
      unzip \
      less \
      groff

# Install kubectl
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl
RUN chmod +x kubectl && mv kubectl /bin/kubectl

# Instal aws cli
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -r aws

# aws-iam-authenticator
RUN curl -o aws-iam-authenticator https://amazon-eks.s3.us-west-2.amazonaws.com/1.15.10/2020-02-22/bin/linux/amd64/aws-iam-authenticator \
    && chmod +x ./aws-iam-authenticator \
    && mv aws-iam-authenticator /usr/bin

RUN adduser --system django

# Requirements are installed here to ensure they will be cached.
COPY ./requirements /requirements
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r /requirements/production.txt \
    && rm -rf /requirements

COPY ./docker/production/django/entrypoint /entrypoint
RUN sed -i 's/\r//' /entrypoint
RUN chmod +x /entrypoint
RUN chown django /entrypoint

COPY ./docker/production/django/start /start
RUN sed -i 's/\r//' /start
RUN chmod +x /start
RUN chown django /start

COPY ./docker/production/django/start_simulator /start_simulator
RUN sed -i 's/\r//' /start_simulator
RUN chmod +x /start_simulator
RUN chown django /start_simulator

COPY ./docker/production/django/start_scheduler /start_scheduler
RUN sed -i 's/\r//' /start_scheduler
RUN chmod +x /start_scheduler

COPY . /app

RUN chown -R django /app

USER django

WORKDIR /app

ENTRYPOINT ["/entrypoint"]
