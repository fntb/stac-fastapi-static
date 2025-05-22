set dotenv-load
set export

set dotenv-path := ".env"

default:
	@just --list

uv:
	@uv -V || echo 'Please install uv: https://docs.astral.sh/uv/getting-started/installation/'


# Install the dependencies
install: uv
	uv sync --frozen --all-extras --all-groups

# Build the package and containerized server image
build: uv
	uv build
	docker build --tag fntb/stac-fastapi-static .

# Publish to pypi
publish: uv
	uv publish --index testpypi

# Starts the server
dev catalog_href=("file://" + justfile_directory() /  "stac_test_catalogs/1000/catalog.json"): uv
	log_level=info \
	environment=dev \
	catalog_href={{catalog_href}} \
	uv run stac_fastapi/static/app.py

# Generates a STAC catalog with roughtly  `n_items` items
generate-test-catalog n_items="1000": uv
	PYTHONPATH=${PYTHONPATH:-}:{{justfile_directory()}} uv run scripts/generate_test_catalog.py {{n_items}}

test n_items="1000": uv
	log_level=info \
	environment=dev \
	n_items={{n_items}} \
	catalog_href={{justfile_directory()}}/stac_test_catalogs/{{n_items}}/catalog.json \
	PYTHONPATH=${PYTHONPATH:-}:{{justfile_directory()}} uv run pytest -v -s --ignore=stac_test_catalogs

# Runs the containerized server
run catalog_href *docker_args: build
	docker run \
	--detach \
	--restart unless-stopped \
	--env environment=prod \
	--env log_level=warning \
	--env catalog_href={{catalog_href}} \
	--volume /tmp:/tmp \
	{{docker_args}} \
	fntb/stac-fastapi-static

clean:
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