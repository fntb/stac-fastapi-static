set dotenv-load

default:
  just --list

# Install dependencies, in a virtual python environment.
install:
	test -d .venv || python3 .venv
	. .venv/bin/activate; \
	pip install -e .[dev,server]

# Starts the server in development mode.
dev catalog_href=("file://" + justfile_directory() /  "stac_test_catalogs" / "1000"):
	test -d .venv || python3 .venv
	. .venv/bin/activate; \
	log_level=INFO \
	environment=dev \
	catalog_href={{catalog_href}} \
	python -m uvicorn stac_fastapi.static.app:app --port ${app_port} --host ${app_host}

test n_items="1000":
	test -d .venv || python3 .venv
	. .venv/bin/activate; \
	log_level=INFO \
	environment=dev \
	n_items={{n_items}} \
	catalog_href=("file://" + justfile_directory() /  "stac_test_catalogs" / "1000") \
	pytest -v -s --ignore=stac_test_catalogs

# Builds the dev docker image, tagged with fntb/stac-fastapi-static:test.
build-test:
	docker build --tag fntb/stac-fastapi-static:test -f test.Dockerfile .

# Generates a STAC catalog with roughtly  \`n_items\` items in a subdirectory for testing purposes.
catalog n_items="1000": build-test
	docker run \
	--rm \
	--volume {{justfile_directory()}}:/app \
	--user $(shell id -u):$(shell id -g) \
	fntb/stac-fastapi-static:test python stac_test_tools ${n_items}

# Runs locust.
test-load: build build-test
	log_level=INFO \
	environment=dev \
	uid=$(shell id -u) \
	gid=$(shell id -g) \
	docker compose run \
	--rm \
	--service-ports test

# Builds the prod docker image, tagged with fntb/stac-fastapi-static.
build:
	docker build --tag fntb/stac-fastapi-static .

# Runs the prod docker image.
run catalog_href +docker_args: build
	docker run \
	--detach \
	--restart unless-stopped \
	--env catalog_href=${catalog_href} \
	--env environment=prod \
	--env log_level=WARNING \
	--env-file=.env \
	--volume /tmp:/tmp \
	--publish ${app_port}:8000 \
	{{docker_args}} \
	fntb/stac-fastapi-static

