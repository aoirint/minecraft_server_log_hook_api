# syntax=docker/dockerfile:1.6
FROM python:3.11

ARG DEBIAN_FRONTEND=noninteractive
ARG PIP_NO_CACHE_DIR=1
ENV PYTHONUNBUFFERED=1
ENV PATH=/home/user/.local/bin:${PATH}

RUN <<EOF
    set -eu

    apt-get update

    apt-get install -y \
        gosu

    apt-get clean
    rm -rf /var/lib/apt/lists/*
EOF

RUN <<EOF
    set -eu

    groupadd -o -g 1000 user
    useradd -m -o -u 1000 -g user user
EOF

ARG POETRY_VERSION=1.7.1
RUN <<EOF
    set -eu

    gosu user pip install "poetry==${POETRY_VERSION}"
EOF

RUN <<EOF
    set -eu

    mkdir -p /code/minecraft_bedrock_log_api
    chown -R user:user /code
EOF

WORKDIR /code/minecraft_bedrock_log_api
ADD ./pyproject.toml ./poetry.lock /code/minecraft_bedrock_log_api/

RUN <<EOF
    set -eu

    gosu user poetry install --only main
EOF

ADD ./minecraft_bedrock_log_api /code/minecraft_bedrock_log_api/minecraft_bedrock_log_api
ADD ./scripts /code/minecraft_bedrock_log_api/scripts

ENTRYPOINT [ "gosu", "user", "poetry", "run", "python", "-m", "minecraft_bedrock_log_api" ]
