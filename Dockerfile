# syntax=docker/dockerfile:1.6
FROM python:3.11

ARG DEBIAN_FRONTEND=noninteractive
ARG PIP_NO_CACHE_DIR=1
ENV PYTHONUNBUFFERED=1
ENV PATH=/code/minecraft_server_log_hook_api/.venv/bin:/home/user/.local/bin:${PATH}

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

ARG POETRY_VERSION=1.8.2
RUN <<EOF
    set -eu

    gosu user pip install "poetry==${POETRY_VERSION}"

    gosu user poetry config virtualenvs.in-project true

    mkdir -p /home/user/.cache/pypoetry/{cache,artifacts}
    chown -R "user:user" /home/user/.cache
EOF

RUN <<EOF
    set -eu

    mkdir -p /code/minecraft_server_log_hook_api
    chown -R user:user /code/minecraft_server_log_hook_api
EOF

WORKDIR /code/minecraft_server_log_hook_api
ADD --chown=1000:1000 ./pyproject.toml ./poetry.lock ./README.md /code/minecraft_server_log_hook_api/
RUN --mount=type=cache,uid=1000,gid=1000,target=/home/user/.cache/pypoetry/cache \
    --mount=type=cache,uid=1000,gid=1000,target=/home/user/.cache/pypoetry/artifacts <<EOF
    set -eu

    gosu user poetry install --no-root --only main
EOF

ADD --chown=1000:1000 ./minecraft_server_log_hook_api /code/minecraft_server_log_hook_api/minecraft_server_log_hook_api
ADD --chown=1000:1000 ./scripts /code/minecraft_server_log_hook_api/scripts
RUN --mount=type=cache,uid=1000,gid=1000,target=/home/user/.cache/pypoetry/cache \
    --mount=type=cache,uid=1000,gid=1000,target=/home/user/.cache/pypoetry/artifacts <<EOF
    set -eu

    gosu user poetry install --only main
EOF

ENTRYPOINT [ "gosu", "user", "poetry", "run", "python", "-m", "minecraft_server_log_hook_api" ]
