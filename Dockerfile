FROM python:3.11.5-bullseye

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

# Install aws cli
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install --update \
    && rm -r aws

# aws-iam-authenticator
RUN curl -o aws-iam-authenticator https://amazon-eks.s3.us-west-2.amazonaws.com/1.15.10/2020-02-22/bin/linux/amd64/aws-iam-authenticator \
    && chmod +x ./aws-iam-authenticator \
    && mv aws-iam-authenticator /usr/bin

RUN adduser --system django

ENV POETRY_HOME="/usr/local"
ENV POETRY_CACHE_DIR="./.cache/poetry"
ENV PATH="/usr/local/bin:$PATH"
ENV PYTHONPATH="$PYTHONPATH:."

EXPOSE 8000

RUN curl -sSL https://install.python-poetry.org | python3 -

RUN mkdir /app
WORKDIR /app

# Copy poetry.lock* in case it doesn't exist in the repo
COPY ./poetry.lock ./pyproject.toml /app/

# Install only the package dependencies here
RUN poetry install --no-root

# Copy the rest of the application
COPY . /app

# Now, run poetry install again to install the application
RUN poetry install

# Copy entry scripts and give execution permissions
RUN sed -i 's/\r//' /app/bin/*.sh
RUN chmod +x /app/bin/*.sh

RUN chown -R django /app

USER django

ENTRYPOINT ["/app/bin/entrypoint.sh"]
