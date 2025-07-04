
import pytest

from urllib.parse import urljoin
import requests
import pystac
import shapely

import stac_pydantic

from stac_fastapi.static.core.lib.datetimes_intersect import (
    datetimes_intersect
)
from stac_fastapi.static.core.lib.geometries_intersect import (
    bbox_intersect,
    geometries_intersect
)
from stac_fastapi.static.core.compat.fromisoformat import fromisoformat

from ..rfc3339 import rfc3339

from ..catalog_tools import (
    pick_item,
    pick_collection,
    walk_items,
    pick_bbox,
    pick_geometry,
    pick_datetimes,
    pick_cql2_filters
)


def test_search_items_by_id(api_base_href: str, catalog: pystac.Catalog):
    item = pick_item(catalog)

    get_request_param = f"ids={item.id}"
    post_request_param = {
        "ids": [item.id]
    }

    for response in (
        requests.get(urljoin(api_base_href, f"search?{get_request_param}")),
        requests.post(urljoin(api_base_href, "search"), json=post_request_param)
    ):
        response.raise_for_status()

        item_collection = pystac.ItemCollection.from_dict(response.json())

        assert len(item_collection.items) == 1
        assert item_collection.items[0].id == item.id


def test_search_items_by_collection(api_base_href: str, catalog: pystac.Catalog):
    collection = pick_collection(catalog)
    collection_item_ids = set(
        item.id
        for item
        in walk_items(collection)
    )

    get_request_param = f"collections={collection.id}"
    post_request_param = {
        "collections": [collection.id]
    }

    for response in (
        requests.get(urljoin(api_base_href, f"search?{get_request_param}")),
        requests.post(urljoin(api_base_href, "search"), json=post_request_param)
    ):
        response.raise_for_status()

        item_collection = pystac.ItemCollection.from_dict(response.json())

        if len(collection_item_ids) > 0:
            assert len(item_collection.items) > 0

        assert set(
            item.id
            for item
            in item_collection.items
        ).issubset(collection_item_ids)


def test_search_items_by_bbox(api_base_href: str, catalog: pystac.Catalog):
    bbox = pick_bbox(catalog)

    bbox_str = ",".join([
        str(coordinate)
        for coordinate in bbox.bounds
    ])

    get_request_param = f"bbox={bbox_str}"
    post_request_param = {
        "bbox": bbox.bounds
    }

    for response in (
        requests.get(urljoin(api_base_href, f"search?{get_request_param}")),
        requests.post(urljoin(api_base_href, "search"), json=post_request_param)
    ):
        response.raise_for_status()

        item_collection = pystac.ItemCollection.from_dict(response.json())

        assert len(item_collection.items) > 0

        for item in item_collection.items:
            assert bbox_intersect(
                bbox.bounds,
                item.bbox
            )


def test_search_items_by_geometry_intersection(api_base_href: str, catalog: pystac.Catalog):
    geometry = pick_geometry(catalog)

    get_request_param = f"intersects={shapely.to_geojson(geometry)}"
    post_request_param = {
        "intersects": shapely.geometry.mapping(geometry)
    }

    for response in (
        requests.get(urljoin(api_base_href, f"search?{get_request_param}")),
        requests.post(urljoin(api_base_href, "search"), json=post_request_param)
    ):
        response.raise_for_status()

        item_collection = pystac.ItemCollection.from_dict(response.json())

        assert len(item_collection.items) > 0

        for item in item_collection.items:
            assert geometries_intersect(
                geometry,
                shapely.geometry.shape(item.geometry)
            )


def test_search_items_by_datetime(api_base_href: str, catalog: pystac.Catalog):
    datetimes_variants = pick_datetimes(catalog)

    for datetimes in datetimes_variants:
        datetime_str = rfc3339.datetime_to_str(datetimes)

        get_request_param = f"datetime={datetime_str}" if datetime_str else ""
        post_request_param = {
            "datetime": datetime_str
        } if datetime_str else {}

        for response in (
            requests.get(urljoin(api_base_href, f"search?{get_request_param}")),
            requests.post(urljoin(api_base_href, "search"), json=post_request_param)
        ):
            response.raise_for_status()

            item_collection = pystac.ItemCollection.from_dict(response.json())

            assert len(item_collection.items) > 0

            for item in item_collection.items:
                item_datetimes = (
                    item.properties.get("start_datetime", None),
                    item.properties.get("end_datetime", None)
                )

                if item_datetimes == (None, None):
                    item_datetimes = fromisoformat(item.datetime)
                else:
                    item_datetimes = tuple(
                        fromisoformat(datetime) for datetime in item_datetimes
                    )

                assert datetimes_intersect(datetimes, item_datetimes)


def test_search_items_limit(api_base_href: str, catalog: pystac.Catalog):
    get_request_param = f"limit=10"
    post_request_param = {"limit": 10}

    for response in (
        requests.get(urljoin(api_base_href, f"search?{get_request_param}")),
        requests.post(urljoin(api_base_href, "search"), json=post_request_param)
    ):
        response.raise_for_status()

        item_collection = pystac.ItemCollection.from_dict(response.json())

        assert len(item_collection.items) <= 10


def test_search_items_by_cql2_filtering(api_base_href: str, catalog: pystac.Catalog):
    (text_filter, json_filter, validate) = pick_cql2_filters(catalog)

    get_request_param = f"filter={text_filter}&filter-lang=cql2-text"
    post_request_param = {
        "filter": json_filter,
        "filter-lang": "cql2-json"
    }

    for response in (
        requests.get(urljoin(api_base_href, f"search?{get_request_param}")),
        requests.post(urljoin(api_base_href, "search"), json=post_request_param)
    ):
        response.raise_for_status()

        item_collection = pystac.ItemCollection.from_dict(response.json())

        assert len(item_collection.items) > 0

        for item in item_collection.items:
            assert validate(item)
