# stac-fastapi-static

<p align="center">
  <img src="https://stacspec.org/public/images-original/STAC-01.png" style="vertical-align: middle; max-width: 400px; max-height: 100px;" height=100 />
  <img src="https://fastapi.tiangolo.com/img/logo-margin/logo-teal.png" alt="FastAPI" style="vertical-align: middle; max-width: 400px; max-height: 100px;" width=200 />
</p>

[Static STAC Catalog](https://github.com/radiantearth/stac-spec/tree/master/catalog-spec) backend for [stac-fastapi](https://github.com/stac-utils/stac-fastapi), the [FastAPI](https://fastapi.tiangolo.com/) implementation of the [STAC API spec](https://github.com/radiantearth/stac-api-spec).

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
| [**Collection Search**](https://github.com/stac-api-extensions/collection-search)                                                                                     | **Yes**                                                                                                                                                                                 |
| [**Filter**](https://github.com/stac-api-extensions/filter)                                                                                                           | **Yes**                                                                                                                                                                                 |
| [**Query**](https://github.com/stac-api-extensions/query)                                                                                                             | **No** - Not intended : _"It is recommended to implement the Filter Extension instead of the Query Extension" [Query Extension homepage](https://github.com/stac-api-extensions/query)_ |
| [**Sort**](https://github.com/stac-api-extensions/sort)                                                                                                               | **No** - Not intended : Hard to implement in an performant enough manner to be viable with a static catalog                                                                             |
| [**Transaction**](https://github.com/stac-api-extensions/transaction) and [**Collection Transaction**](https://github.com/stac-api-extensions/collection-transaction) | **No** - Not intended - Feasible                                                                                                                                                        |
| [**Fields**](https://github.com/stac-api-extensions/fields)                                                                                                           | **No** - Not intended - Feasible                                                                                                                                                        |
| [**Language**](https://github.com/stac-api-extensions/language)                                                                                                       | **No** - Maybe soon ? - Feasible                                                                                                                                                        |

## Use Case

First there are the general STAC use cases : see [the STAC spec website](https://stacspec.org/en).

Then there are the advantages of using a static catalog :

- Easier initial exploration, and easier exploration in general for non-technical people by using [stac-browser](https://radiantearth.github.io/stac-browser/#/?.language=en) _(which can be made beautiful, see [this catalog](https://browser.apex.esa.int/?.language=en) for instance)._
- No database to maintain.

And finally there is what `stac-fastapi-static` brings in addition to the above :

- **plug-and-play** - Just `pip install` or `docker run` the server while pointing it to your deployed or local static catalog.json (see below).
- **very easy to migrate to (and from)** - `stac-fastapi-static` only requires a valid STAC catalog which it won't touch (just read).
- best possible performances **given the difficult limits of filesystem reads** - We tried to take advantage of every details of the STAC spec to speed up requests (see below).

### Performances and limitations

Inherently, building an API on a 100,000s items static STAC catalog is going to be far slower than on a database backed catalog, however the STAC specs defines constraints (and recommendations) that can be abused to design a performant enough API.

The goal was to provide viable performances on a 500,000 item static catalog.

![Response times](./doc/benchmark.png)

_Response times obtained on a (yet) unpublished ~2500 items catalog at the OPGC. These measures were obtained by measuring request times client-side._

**Analysis :**

- `[id=]` - id filtering - time complexity is linear (relative to item / collection count) unless the item / collection id is already cached, then it's fixed (negligible). _An in-memory `walk_path`-`id` cache is built whenever an item is fetched due to a query (even those not using id filtering)._
- `[bbox=]`, `[intersects=]`, and `[datetime=]` - spatio-temporal filtering - complexity depends heavily on the catalog structure. The more deeply nested the catalog is, and the more distant subcollections are (spatially or temporally), the more the complexity will tend to be logarithmic. _This is because whole branches (collections and subcollections) can be skipped based on their extents._ Conversely a single collection is filtered with linear complexity.
- `[filter=]` - cql2 filtering - has linear complexity.
- And pagination complexity tends to logarithmic the more deeply nested the catalog is, and remains linear on a flat collection.

Complex queries (obtained by combining filters) are handled by chaining filters from most to least efficient, thus making even slow cql2 filtering possible.

Slowdowns - such as the one observed in this example - can be caused by :

- Disk read speed : _In this example we encountered read times ranging from .5ms, to some exceptional 500ms, with an eyeballed average at 10ms._

- (Too) complex geometries : _In this example we had some 300,000 points drone flight paths (even using a bbox heuristic, which is done, a false positive results in a geometry intersection computation). **Conversely bbox-like geometries filtering has the same speed as datetime filtering.**_

**Conclusion :**

1. The >100k target is, a-priori, not (yet) achieved in real-world conditions. However it was on a previous randomly generated 125k catalog using bbox geometries and deeply nested collections of 50-100 items.
2. Test on your own catalog :

```bash
just benchmark <path-to-catalog.json>
```

## Usage

### Prefered Method : Containerized API Server

```bash
docker run \
  --env-file .env \
  --env app_port=8000 \
  --env app_host=0.0.0.0 \
	--env reload=false \
  --env log_level=info \
  --env catalog_href=/var/www/html/static/catalog.json \
  --volume /tmp:/tmp \
  --volume /var/www/html/static:/var/www/html/static \
  --publish 8080:8000 \
  ghcr.io/fntb/stac-fastapi-static:1.0.1
```

See [`just run`](./justfile).

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

    app_host: str = "127.0.0.1"
    app_port: int = 8000
    root_path: str = ""

    ...
```

### Test and Develop

```bash
just --list
```

Or see [the Justfile](./justfile).

Release checklist : bump [version](./stac_fastapi/static/__about__.py), build, test build, commit, tag, push, publish to pypi and ghcr.

## History

**stac-fastapi-static** is being actively developped at the [OPGC](https://opgc.uca.fr/) an observatory for the sciences of the universe (OSU) belonging to the [CNRS](https://www.cnrs.fr/en) and the [UCA](https://www.uca.fr/) by its main author Pierre Fontbonne [@fntb](https://github.com/fntb). It was originally reverse engineered from the [stac-fastapi-pgstac](https://github.com/stac-utils/stac-fastapi-pgstac) backend by [developmentseed](https://github.com/developmentseed).

## License

[OPEN LICENCE 2.0](./LICENCE.txt)
