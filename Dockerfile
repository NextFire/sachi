FROM python:3.12@sha256:e83d1f4d0c735c7a54fc9dae3cca8c58473e3b3de08fcb7ba3d342ee75cfc09d

ENV DEBIAN_FRONTEND=noninteractive
ENV POETRY_VIRTUALENVS_IN_PROJECT=1

RUN apt update && \
    apt install -y --no-install-recommends neovim mediainfo && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN pip install poetry && \
    poetry install --without dev --no-root && \
    rm -rf ~/.cache/

COPY sachi sachi
COPY README.md .
RUN poetry install --only-root

ENV EDITOR=nvim
ENTRYPOINT [ "poetry", "run", "sachi" ]
VOLUME [ "/root/.config/sachi" ]
