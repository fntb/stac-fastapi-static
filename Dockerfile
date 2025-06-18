ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-alpine AS build

RUN apk --no-cache add curl

ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

ADD https://astral.sh/uv/install.sh uv-installer.sh
RUN sh uv-installer.sh && \
    rm uv-installer.sh

ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app

COPY ./pyproject.toml ./pyproject.toml
COPY ./uv.lock ./uv.lock

RUN uv sync --compile --locked --no-cache --no-install-project --no-default-groups

FROM python:${PYTHON_VERSION}-alpine

WORKDIR /app

ENV PYTHONPATH="/app/"

COPY --from=build /app/pyproject.toml ./pyproject.toml
COPY --from=build /app/.venv ./.venv

COPY ./README.md ./README.md
COPY ./LICENCE.txt ./LICENCE.txt
COPY ./stac_fastapi ./stac_fastapi

ENTRYPOINT [".venv/bin/python", "stac_fastapi/static/app.py"]