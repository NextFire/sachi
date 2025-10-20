FROM ghcr.io/astral-sh/uv:python3.14-trixie

ENV DEBIAN_FRONTEND=noninteractive

RUN apt update && \
    apt install -y --no-install-recommends neovim mediainfo && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV EDITOR=nvim

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

RUN --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY sachi sachi
COPY README.md .

RUN --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=.git,target=.git \
    --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT [ "sachi" ]
VOLUME [ "/root/.config/sachi" ]
