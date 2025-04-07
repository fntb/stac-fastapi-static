ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS base

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y build-essential
RUN apt-get install -y git
RUN apt-get install -y libgeos-dev
RUN apt-get install -y curl
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs > rustup.sh
RUN sh rustup.sh -y

ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

FROM base AS builder

WORKDIR /app

COPY ./setup.py ./setup.py
COPY ./README.md ./README.md
RUN python -m pip install -e .[server]

COPY . .

ENTRYPOINT ["uvicorn", "stac_fastapi.static.app:app"]
CMD ["--host", "0.0.0.0", "--port", "8080"]
