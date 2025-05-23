ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS base

RUN apt-get update

RUN apt-get upgrade -y
RUN apt-get install -y git build-essential curl
ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/install.sh uv-installer.sh
RUN sh uv-installer.sh && rm uv-installer.sh

ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app

RUN mkdir -p stac_fastapi/static/api stac_fastapi/static/core/compat stac_fastapi/static/core/lib stac_fastapi/static/core/model stac_fastapi/static/core/requests stac_fastapi/static/core/walk_filters

COPY ./README.md ./README.md
COPY ./LICENCE.txt ./LICENCE.txt
COPY ./pyproject.toml ./pyproject.toml
COPY ./stac_fastapi/static/__about__.py ./stac_fastapi/static/__about__.py

RUN uv sync --no-install-project

COPY ./stac_fastapi ./stac_fastapi

RUN uv sync

ENTRYPOINT ["uv", "run", "stac_fastapi/static/app.py"]
