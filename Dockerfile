ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-alpine

RUN apk --no-cache add curl

ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

ADD https://astral.sh/uv/install.sh uv-installer.sh
RUN sh uv-installer.sh && \
    rm uv-installer.sh

ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app

ENV PYTHONPATH="/app/"

COPY ./pyproject.toml ./pyproject.toml
COPY ./uv.lock ./uv.lock

RUN uv sync --compile --locked --no-cache --no-install-project

COPY ./README.md ./README.md
COPY ./LICENCE.txt ./LICENCE.txt
COPY ./pyproject.toml ./pyproject.toml
COPY ./stac_fastapi ./stac_fastapi

ENTRYPOINT [".venv/bin/python", "stac_fastapi/static/app.py"]