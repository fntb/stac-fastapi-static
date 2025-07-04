set dotenv-load
set export

set dotenv-path := ".env"

default:
	@just --list

uv:
	@uv -V || echo 'Please install uv: https://docs.astral.sh/uv/getting-started/installation/'


# Install the dependencies
install *args: uv
	uv sync --all-extras --all-groups {{args}}

# Print version number
version: uv
	#!/usr/bin/bash
	version=`echo "from stac_fastapi.static.__about__ import __version__; print(__version__)" | uv run --no-project -`
	echo stac-fastapi.static ${version}

# Build the package and containerized server image
build: uv
	#!/usr/bin/bash
	version=`echo "from stac_fastapi.static.__about__ import __version__; print(__version__)" | uv run --no-project -`
	uv build
	docker build \
	--tag ghcr.io/fntb/stac-fastapi-static:${version} \
	--label "org.opencontainers.image.source=https://github.com/fntb/stac-fastapi-static" \
	--label "org.opencontainers.image.description=An implementation of STAC API based on the FastAPI framework using a static catalog as backend." \
	--label "org.opencontainers.image.licenses=etalab-2.0" \
	.

# Publish to pypi
publish-pypi: uv
	uv publish

# Publish to ghcr
publish-ghcr:
	#!/usr/bin/bash
	version=`echo "from stac_fastapi.static.__about__ import __version__; print(__version__)" | uv run --no-project -`
	docker push ghcr.io/fntb/stac-fastapi-static:${version}

# Starts the server
dev catalog_href: uv
	log_level=info \
	reload=false \
	catalog_href={{catalog_href}} \
	uv run stac_fastapi/static/app.py

# Clones a catalog for testing purposes
clone *args: uv
	PYTHONPATH=${PYTHONPATH:-}:{{justfile_directory()}} uv run scripts/clone_catalog.py {{args}}

# Sizes a catalog for testing purposes
size *args: uv
	PYTHONPATH=${PYTHONPATH:-}:{{justfile_directory()}} uv run scripts/size_catalog.py {{args}}

test-unit catalog_href: uv
	log_level=info \
	reload=false \
	catalog_href={{catalog_href}} \
	PYTHONPATH=${PYTHONPATH:-}:{{justfile_directory()}} uv run pytest test/unit/ -vv -s --showlocals --api-base-href default

test-functional catalog_href api_base_href="default": uv
	log_level=info \
	reload=false \
	catalog_href={{catalog_href}} \
	PYTHONPATH=${PYTHONPATH:-}:{{justfile_directory()}} uv run pytest test/functional/ -vv -s --showlocals --api-base-href {{api_base_href}}

benchmark catalog_href api_base_href="default": uv
	log_level=info \
	reload=false \
	assume_best_practice_layout=true \
	catalog_href={{catalog_href}} \
	PYTHONPATH=${PYTHONPATH:-}:{{justfile_directory()}} uv run pytest test/performance/ -s --api-base-href {{api_base_href}}

# Runs the containerized server
run catalog_href *docker_args:
	#!/usr/bin/bash
	version=`echo "from stac_fastapi.static.__about__ import __version__; print(__version__)" | uv run --no-project -`
	docker run \
	--env-file .env \
	--env app_port=${app_port:-8000} \
	--env app_host=${app_host:-0.0.0.0} \
	--env reload=false \
	--env log_level=info \
	--env catalog_href={{catalog_href}} \
	--volume /tmp:/tmp \
	--publish ${app_port:-8000}:${app_port:-8000} \
	{{docker_args}} \
	ghcr.io/fntb/stac-fastapi-static:${version}

#	--detach \
#	--restart unless-stopped \

clean:
	@docker image remove ghcr.io/fntb/stac-fastapi-static
	@rm -rf `find . -name __pycache__`
	@rm -f `find . -type f -name '*.py[co]'`
	@rm -f `find . -type f -name '*~'`
	@rm -f `find . -type f -name '.*~'`
	@rm -rf .cache
	@rm -rf .pytest_cache
	@rm -rf .ruff_cache
	@rm -rf htmlcov
	@rm -rf *.egg-info
	@rm -f .coverage
	@rm -f .coverage.*
	@rm -rf build
	@rm -rf dist
	@rm -rf coverage.xml