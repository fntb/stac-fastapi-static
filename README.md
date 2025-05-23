# stac-fastapi-static

<p align="center">
  <img src="https://stacspec.org/public/images-original/STAC-01.png" style="vertical-align: middle; max-width: 400px; max-height: 100px;" height=100 />
  <img src="https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png" alt="FastAPI" style="vertical-align: middle; max-width: 400px; max-height: 100px;" width=200 />
</p>

[Static STAC Catalog](https://github.com/radiantearth/stac-spec/tree/master/catalog-spec) backend for [stac-fastapi](https://github.com/stac-utils/stac-fastapi), the [FastAPI](https://fastapi.tiangolo.com/) implementation of the [STAC API spec](https://github.com/radiantearth/stac-api-spec).

_This project is still in (late) initial development phase._

## Overview

**stac-fastapi-static** is a [stac-fastapi](https://github.com/stac-utils/stac-fastapi) backend built in [FastAPI](https://fastapi.tiangolo.com/). It provides an implementation of the [STAC API spec](https://github.com/radiantearth/stac-api-spec) ready to be deployed on top of a static STAC catalog. The target backend static catalog can be remotely hosted (by any static HTTP server) or locally hosted (filesystem).

## STAC API Support

| Extension                                                                                        | Support |
| ------------------------------------------------------------------------------------------------ | ------- |
| [**Core**](https://github.com/radiantearth/stac-api-spec/tree/release/v1.0.0/core)               | **Yes** |
| [**Item Search**](https://github.com/radiantearth/stac-api-spec/tree/release/v1.0.0/item-search) | **Yes** |

### STAC API Extensions Support

From [STAC API Extensions](https://stac-api-extensions.github.io/) page :

| Extension                                                                                                                                                             | Support                                                                                                                                                                                 |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [**Query**](https://github.com/stac-api-extensions/query)                                                                                                             | **No** - Not intended : _"It is recommended to implement the Filter Extension instead of the Query Extension" [Query Extension homepage](https://github.com/stac-api-extensions/query)_ |
| [**Sort**](https://github.com/stac-api-extensions/sort)                                                                                                               | **No** - Not intended : Hard to implement in an performant enough manner to be viable with a static catalog                                                                             |
| [**Transaction**](https://github.com/stac-api-extensions/transaction) and [**Collection Transaction**](https://github.com/stac-api-extensions/collection-transaction) | **No** - Not intended - Feasible                                                                                                                                                        |
| [**Fields**](https://github.com/stac-api-extensions/fields)                                                                                                           | **No** - Not intended - Feasible                                                                                                                                                        |
| [**Filter**](https://github.com/stac-api-extensions/filter)                                                                                                           | **Yes**                                                                                                                                                                                 |
| [**Collection Search**](https://github.com/stac-api-extensions/collection-search)                                                                                     | **Yes**                                                                                                                                                                                 |
| [**Language**](https://github.com/stac-api-extensions/language)                                                                                                       | **No** - Maybe soon ? - Feasible                                                                                                                                                        |

## Use Cases & Limitations

The appeal of instanciating a STAC API directly on top of a static catalog is obvious. However the performance issue will make or break this project.

Our goal is to provide viable performances on a 500,000 item static catalog.

### Design Choices, Performances and limitations

Inherently, building an API on a 100,000s items static STAC catalog is going to be far slower than on a database backed catalog, however the STAC specs defines constraints (and recommendations) that can be abused to design a performant enough API.

_todo : Include data plots from locust tests on big catalogs._

## Usage

### Prefered Method : Containerized API Server

```bash
docker run \
	--env-file .env \
	--env app_port=8000 \
	--env environment=prod \
	--env log_level=warning \
	--env catalog_href=<catalog_url> \
	--volume /tmp:/tmp \
	--publish 8000:8000 \
	ghcr.io/fntb/stac-fastapi-static: latest
```

Note :

- `--volume <path-to-catalog-directory>:/app/catalog/` and `--env catalog_href=file:///app/catalog/catalog.json` to serve a local catalog
- See [the Justfile](./justfile).

### Alternative Method : Python Packaged API Server

Install, create a `dotenv` configuration file (or pass configuration options as env variables), and run :

```bash
pip install stac-fastapi-static

# either
touch .env
stac-fastapi-static

# or
<option>=<value> stac-fastapi-static
```

### Configuration Options

See [the Settings model](./stac_fastapi/static/api/config.py).

Amongst other :

```python
class Settings(ApiSettings):
    # https://docs.pydantic.dev/latest/concepts/pydantic_settings/

    ...

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    root_path: str = ""

    ...
```

### Test and Develop

```bash
just --list
```

Or see [the Justfile](./justfile).

Release checklist : bump [version](./stac_fastapi/static/__about__.py), build, commit, tag, push, publish to pypi and ghcr.

## History

**stac-fastapi-static** is being actively developped at the [OPGC](https://opgc.uca.fr/) an observatory for the sciences of the universe (OSU) belonging to the [CNRS](https://www.cnrs.fr/en) and the [UCA](https://www.uca.fr/) by its main author Pierre Fontbonne [@fntb](https://github.com/fntb). It was originally reverse engineered from the [stac-fastapi-pgstac](https://github.com/stac-utils/stac-fastapi-pgstac) backend by [developmentseed](https://github.com/developmentseed).

## License

[OPEN LICENCE 2.0](./LICENCE.txt)
