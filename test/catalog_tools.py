from typing import (
    Tuple,
    List,
    Iterator,
    Iterable,
    cast,
    List,
    Dict,
    Any,
    Optional
)

import random
from itertools import islice

import pystac
import pystac_client
import shapely

from stac_pydantic.shared import BBox
from geojson_pydantic.geometries import Geometry
import datetime


def walk_items(catalog: pystac.Catalog | pystac_client.Client) -> Iterator[pystac.Item]:
    if isinstance(catalog, (pystac.Catalog, pystac.Collection, pystac.Item)):
        yield from _walk_catalog_items(catalog)
    else:
        raise NotImplementedError("Cannot walk a STAC API")


def walk_collections(catalog: pystac.Catalog | pystac_client.Client) -> Iterator[pystac.Catalog | pystac.Collection]:
    if isinstance(catalog, (pystac.Catalog, pystac.Collection, pystac.Item)):
        walk = _walk_catalog_collections(catalog)
    else:
        raise NotImplementedError("Cannot walk a STAC API")

    for collection in walk:
        if collection != catalog:
            yield collection


def random_walk_items(catalog: pystac.Catalog | pystac_client.Client) -> Iterator[pystac.Item]:
    if isinstance(catalog, (pystac.Catalog, pystac.Collection, pystac.Item)):
        yield from _random_walk_catalog_items(catalog)
    else:
        raise NotImplementedError("Cannot walk a STAC API")


def random_walk_collections(catalog: pystac.Catalog | pystac_client.Client) -> Iterator[pystac.Catalog | pystac.Collection]:
    if isinstance(catalog, (pystac.Catalog, pystac.Collection, pystac.Item)):
        walk = _random_walk_catalog_collections(catalog)
    else:
        raise NotImplementedError("Cannot walk a STAC API")

    for collection in walk:
        if collection != catalog:
            yield collection


def _walk_catalog_items(catalog: pystac.Catalog) -> Iterator[pystac.Item]:
    for link in catalog.links:
        if link.rel == "item":
            yield link.resolve_stac_object(catalog.get_root()).target
        elif link.rel == "child":
            yield from _walk_catalog_items(link.resolve_stac_object(catalog.get_root()).target)


def _walk_catalog_collections(catalog: pystac.Catalog) -> Iterator[pystac.Catalog | pystac.Collection]:
    yield catalog

    for link in catalog.links:
        if link.rel == "child":
            yield from _walk_catalog_collections(link.resolve_stac_object(catalog.get_root()).target)


def _random_walk_catalog_items(catalog: pystac.Catalog) -> Iterator[pystac.Item]:
    for collection in _random_walk_catalog_collections(catalog):
        item_candidate_links = [
            link
            for link in collection.links
            if link.rel in ["item"]
        ]

        if item_candidate_links:
            next_state_link = random.choice(item_candidate_links)
            yield next_state_link.resolve_stac_object(collection.get_root()).target


def _random_walk_catalog_collections(catalog: pystac.Catalog) -> Iterator[pystac.Catalog | pystac.Collection]:
    def pick_next_state(state: pystac.Catalog | pystac.Collection) -> pystac.Catalog | pystac.Collection:
        rels = ["parent", "child"] if state != catalog else ["child"]

        next_state_candidate_links = [
            link
            for link in state.links
            if link.rel in rels
        ]

        next_state_link = random.choice(next_state_candidate_links)

        return next_state_link.resolve_stac_object(state.get_root()).target

    state = catalog
    while True:
        yield (state := pick_next_state(state))


def pick_item(catalog: pystac.Catalog | pystac_client.Client) -> pystac.Item:
    return next(random_walk_items(catalog))


def pick_collection(catalog: pystac.Catalog | pystac_client.Client) -> pystac.Collection:
    return next(random_walk_collections(catalog))


def pick_items(catalog: pystac.Catalog | pystac_client.Client, n: int = 1) -> List[pystac.Item]:
    return list(islice(random_walk_items(catalog), n))


def pick_collections(catalog: pystac.Catalog | pystac_client.Client, n: int = 1) -> List[pystac.Collection]:
    return list(islice(random_walk_collections(catalog), n))


def pick_bbox(catalog: pystac.Catalog | pystac_client.Client) -> shapely.Geometry:
    item = pick_item(catalog)

    return shapely.box(*item.bbox)


def pick_geometry(catalog: pystac.Catalog | pystac_client.Client) -> shapely.Geometry:
    item = pick_item(catalog)

    return shapely.geometry.shape(item.geometry)


def _fromisoformat(datetime_s: str) -> datetime.datetime:
    if not datetime_s.endswith("Z"):
        return datetime.datetime.fromisoformat(datetime_s)
    else:
        return datetime.datetime.fromisoformat(datetime_s.rstrip("Z") + "+00:00")


def pick_datetimes(catalog: pystac.Catalog | pystac_client.Client) -> Tuple[Tuple[None | datetime.datetime, None | datetime.datetime]]:
    items = (pick_item(catalog), pick_item(catalog))

    start_datetime = min(
        _fromisoformat(
            item.properties.get(
                "start_datetime", item.datetime and item.datetime.isoformat()
            )
        )
        for item
        in items
    )

    end_datetime = max(
        _fromisoformat(
            item.properties.get(
                "end_datetime", item.datetime and item.datetime.isoformat()
            )
        )
        for item
        in items
    )

    return (
        (None, None),
        (start_datetime, None),
        (None, end_datetime),
        (start_datetime, end_datetime),
        (start_datetime, start_datetime)
    )


def pick_cql2_filters(catalog: pystac.Catalog | pystac_client.Client) -> Tuple[str, Dict]:
    item = pick_item(catalog)

    if (value := item.properties.get("title")):
        property = "title"
    elif (value := item.properties.get("description")):
        property = "description"
    else:
        for (candidate_property, candidate_value) in item.properties.items():
            if isinstance(candidate_value, str):
                property = candidate_property
                value = candidate_value
                break
        else:
            raise Exception("No candidate property found")

    return (f"{property} LIKE '{value[:3]}%'", {"op": "like", "args": [{"property": property}, f"{value[:3]}%"]})
