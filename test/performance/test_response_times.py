from typing import (
    Any,
    Optional
)

import logging
import time
from urllib.parse import urljoin
import random
import math

import pytest

import requests
import pystac
import shapely

from ..rfc3339 import rfc3339

from ..catalog_tools import (
    pick_item,
    pick_collection,
    pick_bbox,
    pick_geometry,
    pick_datetimes,
    pick_cql2_filters
)

from .conftest import (
    Benchmark
)

logger = logging.getLogger(__name__)

execution_number = 100
execution_number_slow = 20
limit_matches = 10


def timed_request(
    api_base_href: str,
    benchmark: Benchmark,
    collection_group: str,
    parametrized_href: str,
    random_pick: Optional[Any] = None
):

    start = time.time()
    response = requests.get(urljoin(api_base_href, parametrized_href))
    end = time.time()

    response_time = (end - start) * 1000

    response.raise_for_status()

    benchmark.collect(
        collection_group,
        response_time
    )


@pytest.mark.parametrize("execution_number", range(execution_number))
def test_search_items_by_datetime(api_base_href: str, catalog: pystac.Catalog, benchmark: Benchmark, execution_number):
    datetimes_variants = pick_datetimes(catalog)
    datetimes = random.choice(datetimes_variants)
    datetime_str = rfc3339.datetime_to_str(datetimes)

    timed_request(
        api_base_href,
        benchmark,
        "/search?[datetime=]",
        f"search?limit={limit_matches}&datetime={datetime_str}" if datetime_str else "search?"
    )


@pytest.mark.parametrize("execution_number", range(execution_number))
def test_search_items_by_bbox(api_base_href: str, catalog: pystac.Catalog, benchmark: Benchmark, execution_number):
    bbox = pick_bbox(catalog)

    bbox_str = ",".join([
        str(coordinate)
        for coordinate in bbox.bounds
    ])

    timed_request(
        api_base_href,
        benchmark,
        "/search?[bbox=]",
        f"search?limit={limit_matches}&bbox={bbox_str}"
    )


@pytest.mark.parametrize("execution_number", range(execution_number))
def test_search_items_by_geometry_intersection(api_base_href: str, catalog: pystac.Catalog, benchmark: Benchmark, execution_number):
    geometry = pick_geometry(catalog)

    timed_request(
        api_base_href,
        benchmark,
        "/search?[intersects=]",
        f"search?limit={limit_matches}&intersects={shapely.to_geojson(geometry)}"
    )


@pytest.mark.parametrize("execution_number", range(execution_number))
def test_search_items_by_id(api_base_href: str, catalog: pystac.Catalog, benchmark: Benchmark, execution_number):
    item = pick_item(catalog)

    timed_request(
        api_base_href,
        benchmark,
        "/search?[ids=]",
        f"search?limit={limit_matches}&ids={item.id}"
    )


@pytest.mark.parametrize("execution_number", range(execution_number))
def test_search_items_by_collection(api_base_href: str, catalog: pystac.Catalog, benchmark: Benchmark, execution_number):
    collection = pick_collection(catalog)

    timed_request(
        api_base_href,
        benchmark,
        "/search?[collections=]",
        f"search?limit={limit_matches}&collections={collection.id}"
    )


@pytest.mark.parametrize("execution_number", range(math.ceil(execution_number_slow)))
def test_search_items_by_cql2_filtering(api_base_href: str, catalog: pystac.Catalog, benchmark: Benchmark, execution_number):
    (text_filter, json_filter, validate) = pick_cql2_filters(catalog)

    timed_request(
        api_base_href,
        benchmark,
        "/search?[filter=]",
        f"search?limit={limit_matches}&filter={text_filter}&filter-lang=cql2-text"
    )


@pytest.mark.parametrize("execution_number", range(math.ceil(execution_number_slow)))
def test_search_items_by_cql2_filtering_after_collection_filtering(api_base_href: str, catalog: pystac.Catalog, benchmark: Benchmark, execution_number):
    collection = pick_collection(catalog)

    try:
        (text_filter, json_filter, validate) = pick_cql2_filters(collection)
    except IndexError:
        return

    timed_request(
        api_base_href,
        benchmark,
        "/search?[filter=]&[collections=]",
        f"search?limit={limit_matches}&filter={text_filter}&filter-lang=cql2-text&collections={collection.id}"
    )
