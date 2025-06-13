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


def pick_bbox(catalog: pystac.Catalog | pystac_client.Client) -> shapely.Polygon:
    item = pick_item(catalog)

    if item.bbox:
        bbox = shapely.geometry.box(*item.bbox)
    else:
        bbox = shapely.geometry.box(shapely.geometry.shape(item.geometry).bounds)

    return bbox


def pick_geometry(catalog: pystac.Catalog | pystac_client.Client) -> shapely.Geometry:
    item = pick_item(catalog)

    if item.bbox:
        geometry = shapely.geometry.box(*item.bbox)
    else:
        geometry = shapely.geometry.shape(item.geometry)

    return geometry


def pick_datetimes(catalog: pystac.Catalog | pystac_client.Client) -> Tuple[Tuple[None | datetime.datetime, None | datetime.datetime]]:
    item = pick_item(catalog)

    if item.datetime:
        start_datetime = item.datetime - datetime.timedelta(days=1)
        end_datetime = item.datetime + datetime.timedelta(days=1)
    else:
        start_datetime = item.properties.get("start_datetime") - datetime.timedelta(days=1)
        end_datetime = item.properties.get("end_datetime") + datetime.timedelta(days=1)

    return (
        (None, None),
        (start_datetime, None),
        (None, end_datetime),
        (start_datetime, end_datetime),
        (start_datetime, start_datetime)
    )


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
