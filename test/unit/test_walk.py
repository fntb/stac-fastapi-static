import math

import pystac


from ..conftest import (
    settings
)

from ..catalog_tools import (
    walk_collections as walk_static_collections,
    walk_items as walk_static_items,
    pick_collections,
    pick_items,
)

from stac_fastapi.static.core import (
    walk,
    walk_collections,
    walk_items,
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
