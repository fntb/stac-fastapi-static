import math

import pytest
import pystac
import shapely

from stac_pydantic.item import Item
from stac_pydantic.collection import Collection
from stac_pydantic.shared import BBox
from geojson_pydantic.geometries import Geometry

from ..conftest import (
    settings
)

from ..catalog_tools import (
    walk_collections as walk_static_collections,
    walk_items as walk_static_items,
    pick_collections,
    pick_items,
    pick_datetimes
)

from stac_fastapi.static.core import (
    walk,
    make_walk_pagination_filter,
    make_walk_datetime_filter,
    make_walk_temporal_extent_filter,
    make_walk_item_cql2_filter,
    walk_collections,
    walk_items
)


from stac_fastapi.static.core.walk_filters.temporal_filters import (
    make_match_datetime,
    make_match_temporal_extent
)
from stac_fastapi.static.core.walk_filters.cql2_filter import (
    make_match_item_cql2
)

from stac_fastapi.static.core.requests import (
    file_path_to_file_uri as _file_path_to_file_uri,
    is_file_uri
)


def file_path_to_file_uri(href: str) -> str:
    if is_file_uri(href):
        return _file_path_to_file_uri(href)
    else:
        return href


def test_walk_everything(catalog: pystac.Catalog, catalog_href: str, session):
    hrefs = set(
        file_path_to_file_uri(object.get_self_href())
        for object
        in walk_static_collections(catalog)
    )
    hrefs |= set(
        file_path_to_file_uri(object.get_self_href())
        for object
        in walk_static_items(catalog)
    )

    walked_hrefs = set(
        link.href
        for link
        in walk(file_path_to_file_uri(catalog_href), session=session, settings=settings)
    )

    assert hrefs == walked_hrefs


def test_walk_order(catalog: pystac.Catalog, catalog_href: str, session):
    walked_paths = [
        link.walk_path
        for link
        in walk(file_path_to_file_uri(catalog_href), session=session, settings=settings)
    ]

    sorted_walked_paths = sorted(
        walked_paths
    )

    assert walked_paths == sorted_walked_paths


def test_walk_pagination_filter(catalog: pystac.Catalog, catalog_href: str, session):
    walk_paths = [
        link.walk_path
        for link
        in walk(file_path_to_file_uri(catalog_href), session=session, settings=settings)
    ]

    ref_walk_path_i = math.floor(len(walk_paths) / 2)
    ref_walk_path = walk_paths[ref_walk_path_i]

    walk_pagination_filter = make_walk_pagination_filter(
        start=ref_walk_path
    )

    filtered_walk = walk(file_path_to_file_uri(catalog_href), session=session, settings=settings)
    filtered_walk = walk_pagination_filter(filtered_walk)

    assert list(map(
        lambda walk_result: walk_result.walk_path,
        filtered_walk
    )) == walk_paths[ref_walk_path_i:]

    walk_pagination_filter = make_walk_pagination_filter(
        end=ref_walk_path
    )

    filtered_walk = walk(file_path_to_file_uri(catalog_href), session=session, settings=settings)
    filtered_walk = walk_pagination_filter(filtered_walk)

    assert list(map(
        lambda walk_result: walk_result.walk_path,
        filtered_walk
    )) == walk_paths[:(ref_walk_path_i + 1)]


def test_walk_collections(catalog: pystac.Catalog, catalog_href: str, session):
    collections = walk_static_collections(catalog)

    filtered_walk = walk_collections(
        file_path_to_file_uri(catalog_href),
        session=session,
        settings=settings
    )

    assert set(
        walk_result.resolve_id()
        for walk_result
        in filtered_walk
    ) == set(
        collection.id
        for collection
        in collections
    )

    collections = pick_collections(catalog, 5)

    filtered_walk = walk_collections(
        file_path_to_file_uri(catalog_href),
        [
            collection.id
            for collection
            in collections

        ],
        session=session,
        settings=settings
    )

    assert set(
        walk_result.resolve_id()
        for walk_result
        in filtered_walk
    ) == set(
        collection.id
        for collection
        in collections
    )


def test_walk_items(catalog: pystac.Catalog, catalog_href: str, session):
    items = walk_static_items(catalog)

    filtered_walk = walk_items(
        file_path_to_file_uri(catalog_href),
        session=session,
        settings=settings
    )

    assert set(
        walk_result.resolve_id()
        for walk_result
        in filtered_walk
    ) == set(
        item.id
        for item
        in items
    )

    items = pick_items(catalog, 5)

    filtered_walk = walk_items(
        file_path_to_file_uri(catalog_href),
        [
            item.id
            for item
            in items

        ],
        session=session,
        settings=settings
    )

    assert set(
        walk_result.resolve_id()
        for walk_result
        in filtered_walk
    ) == set(
        item.id
        for item
        in items
    )


def test_walk_temporal_filters(catalog: pystac.Catalog, catalog_href: str, session):
    datetimes = pick_datetimes(catalog)

    for datetime in datetimes:
        match_datetime = make_match_datetime(datetime)
        match_temporal_extent = make_match_temporal_extent(datetime)

        expected_matching_items = set(
            item.id
            for item
            in walk_static_items(catalog)
            if match_datetime(Item.model_validate(item.to_dict(include_self_link=False)))
        )

        assert expected_matching_items

        expected_matching_collections = set(
            collection.id
            for collection
            in walk_static_collections(catalog)
            if match_temporal_extent(Collection.model_validate(collection.to_dict(include_self_link=False)))
        )

        assert expected_matching_collections

        walk_datetime_filter = make_walk_datetime_filter(
            datetime=datetime
        )

        walk_temporal_extent_filter = make_walk_temporal_extent_filter(
            datetime=datetime,
        )

        matched_items = set(
            walk_result.resolve_id()
            for walk_result
            in walk_datetime_filter(
                walk(
                    file_path_to_file_uri(catalog_href),
                    session=session,
                    settings=settings
                )
            )
            if walk_result.type is Item
        )

        matched_collections = set(
            walk_result.resolve_id()
            for walk_result
            in walk_temporal_extent_filter(
                walk_collections(
                    file_path_to_file_uri(catalog_href),
                    session=session,
                    settings=settings
                )
            )
            if walk_result.type is Collection
        )

        assert len(matched_items) > 0
        assert matched_items <= expected_matching_items

        assert matched_collections
        assert matched_collections <= expected_matching_collections


def test_cql2_filter(catalog: pystac.Catalog, catalog_href: str, session):
    items = pick_items(catalog, 5)

    for item in items:
        item.properties["test"] = "test"

        match_cql2 = make_match_item_cql2("test = 'test'")

        assert match_cql2(Item.model_validate(item.to_dict()))
