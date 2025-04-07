#!make

ifneq (,$(wildcard ./.env))
	include .env
	export
endif

n_items ?= 1000

.PHONY: install
install:
	test -d .venv || python3 .venv
	. .venv/bin/activate; \
	pip install -e .[dev,server]

help:
	@echo "------------"
	@echo "Dev Targets"
	@echo "------------"
	@echo " install    - Install dependencies, in a virtual python environment."
	@echo " dev        - Starts the server in development mode."
	@echo "------------"
	@echo "Test Targets"
	@echo "------------"
	@echo " test       - Runs the test suite."
	@echo " image:test - Builds the dev docker image, tagged with fntb/stac-fastapi-static:test."
	@echo " catalog    - Generates a STAC catalog with roughtly  \`n_items\` items in a subdirectory for testing purposes."
	@echo " test-load  - Runs locust."
	@echo "------------"
	@echo "Build & Prod Targets"
	@echo "------------"
	@echo " image      - Builds the prod docker image, tagged with fntb/stac-fastapi-static."
	@echo " run        - Runs the prod docker image."

.PHONY: dev
dev:
	test -d .venv || python3 .venv
	. .venv/bin/activate; \
	n_items=${n_items} \
	catalog_href=${catalog_href} \
	log_level=INFO \
	environment=dev \
	python -m uvicorn stac_fastapi.static.app:app --host ${app_host} --port ${app_port}

.PHONY: test
test:
	test -d .venv || python3 .venv
	. .venv/bin/activate; \
	n_items=${n_items} \
	catalog_href=${catalog_href} \
	log_level=INFO \
	environment=dev \
	pytest -v -s --ignore=stac_test_catalogs

.PHONY: image\:test
image\:test:
	docker build --tag fntb/stac-fastapi-static:test -f test.Dockerfile .

.PHONY: catalog
catalog: image\:test
	docker run \
	--rm \
	--volume $(shell pwd):/app \
	--user $(shell id -u):$(shell id -g) \
	fntb/stac-fastapi-static:test python stac_test_tools ${n_items}

.PHONY: test-load
test-load: image image\:test
	n_items=${n_items} \
	log_level=INFO \
	environment=dev \
	uid=$(shell id -u) \
	gid=$(shell id -g) \
	docker compose run \
	--rm \
	--service-ports test

.PHONY: image
image:
	docker build --tag fntb/stac-fastapi-static .

ifdef catalog_file
catalog_volume = --volume $(dir ${catalog_file}):$(dir ${catalog_file})
catalog_href = file://${catalog_file}
else
catalog_volume = 
endif

.PHONY: run
run: image
	docker run \
	--detach \
	--restart unless-stopped \
	--env catalog_href=${catalog_href} \
	--env environment=prod \
	--env log_level=WARNING \
	--volume /tmp:/tmp \
	${catalog_volume} \
	--publish ${app_port}:8080 \
	fntb/stac-fastapi-static --host 0.0.0.0 --port 8080

