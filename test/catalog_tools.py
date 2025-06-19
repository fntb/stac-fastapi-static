from typing import (
    Tuple,
    List,
    Iterator,
    Iterable,
    cast,
    List,
    Dict,
    Any,
    Optional,
    Callable
)

import random
from itertools import islice

import pystac
import pystac_client
import shapely

from stac_pydantic.shared import BBox
from geojson_pydantic.geometries import Geometry
import datetime

from stac_fastapi.static.core.compat import fromisoformat


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
    for (i, item) in enumerate(random_walk_items(catalog)):
        if i >= 9:
            return item


def pick_collection(catalog: pystac.Catalog | pystac_client.Client) -> pystac.Collection:
    for (i, collection) in enumerate(random_walk_collections(catalog)):
        if i >= 9:
            return collection


def pick_items(catalog: pystac.Catalog | pystac_client.Client, n: int = 1) -> List[pystac.Item]:
    items = []

    for (i, item) in enumerate(random_walk_items(catalog)):
        if i >= 9 and i < 9 + n:
            items.append(item)
        if i >= 9 + n:
            break

    return items


def pick_collections(catalog: pystac.Catalog | pystac_client.Client, n: int = 1) -> List[pystac.Collection]:
    collections = []

    for (i, collection) in enumerate(random_walk_collections(catalog)):
        if i >= 9 and i < 9 + n:
            collections.append(collection)
        if i >= 9 + n:
            break

    return collections


def pick_bbox(catalog: pystac.Catalog | pystac_client.Client) -> shapely.Polygon:
    item = pick_item(catalog)

    def get_item_bbox(item: pystac.Item) -> shapely.Polygon | None:
        if item.bbox:
            return shapely.geometry.box(*item.bbox)
        elif item.geometry:
            return shapely.geometry.box(shapely.geometry.shape(item.geometry).bounds)
        else:
            return None

    if bbox := get_item_bbox(item):
        return bbox

    for item in walk_items(catalog):
        if bbox := get_item_bbox(item):
            return bbox

    raise ValueError("Catalog doesn't have any valid bbox")


def pick_geometry(catalog: pystac.Catalog | pystac_client.Client) -> shapely.Geometry:
    item = pick_item(catalog)

    def get_item_geometry(item: pystac.Item) -> shapely.Geometry | None:
        if item.bbox:
            return shapely.geometry.box(*item.bbox)
        elif item.geometry:
            return shapely.geometry.shape(item.geometry)
        else:
            return None

    if geometry := get_item_geometry(item):
        return geometry

    for item in walk_items(catalog):
        if geometry := get_item_geometry(item):
            return geometry

    raise ValueError("Catalog doesn't have any valid geometry")


def pick_datetimes(catalog: pystac.Catalog | pystac_client.Client) -> Tuple[Tuple[None | datetime.datetime, None | datetime.datetime]]:
    item = pick_item(catalog)

    def get_item_datetimes(item: pystac.Item) -> Tuple[datetime.datetime, datetime.datetime] | None:
        if item.datetime:
            return [item.datetime, item.datetime]
        elif (start_datetime := item.properties.get("start_datetime")) is not None and (end_datetime := item.properties.get("end_datetime")) is not None:
            if isinstance(start_datetime, str):
                start_datetime = fromisoformat(start_datetime)
            if isinstance(end_datetime, str):
                end_datetime = fromisoformat(end_datetime)
            return [start_datetime, end_datetime]
        else:
            return None

    def make_all_datetimes_variants(datetimes:  Tuple[datetime.datetime, datetime.datetime]) -> Tuple[Tuple[None | datetime.datetime, None | datetime.datetime]]:
        [start_datetime, end_datetime] = datetimes

        return (
            (None, None),
            (start_datetime - datetime.timedelta(days=1), None),
            (None, end_datetime + datetime.timedelta(days=1)),
            (start_datetime - datetime.timedelta(days=1), end_datetime + datetime.timedelta(days=1)),
        )

    if datetimes := get_item_datetimes(item):
        return make_all_datetimes_variants(datetimes)

    for item in walk_items(catalog):
        if datetimes := get_item_datetimes(item):
            return make_all_datetimes_variants(datetimes)

    raise ValueError("Catalog doesn't have any valid datetimes")


def pick_cql2_filters(catalog: pystac.Catalog | pystac_client.Client) -> Tuple[str, Dict, Callable[[pystac.Item], bool]]:
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

    text_filter = f"{property} LIKE '{value[:3]}%'"
    json_filter = {"op": "like", "args": [{"property": property}, f"{value[:3]}%"]}

    def validate(item: pystac.Item) -> bool:
        candidate_value = item.properties.get(property, None)

        return isinstance(candidate_value, str) and candidate_value.startswith(value[:3])

    return (text_filter, json_filter, validate)
