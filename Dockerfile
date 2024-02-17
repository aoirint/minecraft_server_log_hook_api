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

    groupadd --non-unique --gid 1000 user
    useradd --non-unique --uid 1000 --gid 1000 --create-home user
EOF

ARG POETRY_VERSION=1.7.1
RUN <<EOF
    set -eu

    gosu user pip install "poetry==${POETRY_VERSION}"
EOF

RUN <<EOF
    set -eu

    mkdir -p /code/minecraft_server_log_hook_api
    chown -R user:user /code
EOF

WORKDIR /code/minecraft_server_log_hook_api
ADD ./pyproject.toml ./poetry.lock /code/minecraft_server_log_hook_api/

RUN <<EOF
    set -eu

    gosu user poetry install --only main
EOF

ADD ./minecraft_server_log_hook_api /code/minecraft_server_log_hook_api/minecraft_server_log_hook_api
ADD ./scripts /code/minecraft_server_log_hook_api/scripts

ENTRYPOINT [ "gosu", "user", "poetry", "run", "python", "-m", "minecraft_server_log_hook_api" ]
