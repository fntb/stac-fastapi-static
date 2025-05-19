from typing import (
    Optional,
    List,
    Any,
    Union,
    Tuple,
    Dict,
    Literal
)

import datetime as datetimelib

from stac_pydantic.shared import BBox
from stac_pydantic.api.search import Intersection

from stac_pydantic.item_collection import ItemCollection
from stac_pydantic.item import Item
from stac_pydantic.collection import Collection
from stac_pydantic.catalog import Catalog

from requests import Session

from .walk import (
    WalkSettings,
    chain_walks,
    walk
)

from .walk_filters import (
    chain_walk_filters,
    make_walk_pagination_filter,
    make_walk_temporal_extent_filter,
    make_walk_spatial_extent_filter,
    make_walk_bbox_filter,
    make_walk_collection_cql2_filter,
    make_walk_datetime_filter,
    make_walk_depth_filter,
    make_walk_geometry_filter,
    make_walk_item_cql2_filter
)

from .walk_items import (
    walk_items,
    make_walk_filter_items,
    get_item as _get_item
)

from .walk_collections import (
    walk_collections,
    get_collection as _get_collection
)

from .pagination import (
    WalkMarker,
    WalkPage
)


class ClientSettings(WalkSettings):
    assume_extent_spec: bool
    catalog_href: str


Datetime = Union[
    datetimelib.datetime,
    Tuple[datetimelib.datetime, datetimelib.datetime],
    Tuple[datetimelib.datetime, None],
    Tuple[None, datetimelib.datetime],
]


def search_items(
    collections: Optional[List[str]] = None,
    ids: Optional[List[str]] = None,
    bbox: Optional[BBox] = None,
    intersects: Optional[Intersection] = None,
    datetime: Optional[Datetime] = None,
    walk_marker: Optional[WalkMarker] = None,
    limit: Optional[int] = 100,
    filter: Optional[Union[str, Dict]] = None,
    *,
    settings: ClientSettings,
    session: Session
) -> WalkPage:

    if ids:
        walk_filter_chain = chain_walk_filters(
            make_walk_pagination_filter(
                start=walk_marker.start if walk_marker else None,
                end=walk_marker.end if walk_marker else None
            )
        )

        _walk = walk_items(
            settings.catalog_href,
            item_ids=ids,
            collection_ids=collections,
            session=session,
            settings=settings
        )
    else:
        walk_filter_chain = chain_walk_filters(
            make_walk_pagination_filter(
                start=walk_marker.start if walk_marker else None,
                end=walk_marker.end if walk_marker else None
            ),
            make_walk_spatial_extent_filter(
                geometry=bbox or intersects,
                assume_extent_spec=settings.assume_extent_spec
            ),
            make_walk_temporal_extent_filter(
                datetime,
                assume_extent_spec=settings.assume_extent_spec
            ),
            make_walk_filter_items(),
            make_walk_datetime_filter(
                datetime,
                assume_extent_spec=settings.assume_extent_spec
            ),
            make_walk_bbox_filter(
                bbox,
                assume_extent_spec=settings.assume_extent_spec
            ),
            make_walk_geometry_filter(
                intersects,
                assume_extent_spec=settings.assume_extent_spec
            ),
            make_walk_item_cql2_filter(filter)
        )

        if collections:
            _walk = chain_walks(
                *(
                    walk(
                        collection,
                        session=session,
                        settings=settings
                    )
                    for collection
                    in walk_collections(
                        settings.catalog_href,
                        collection_ids=collections,
                        session=session,
                        settings=settings
                    )
                )
            )
        else:
            _walk = walk(
                settings.catalog_href,
                session=session,
                settings=settings
            )

    filtered_walk = walk_filter_chain(_walk)

    page = WalkPage.paginate(
        filtered_walk,
        walk_marker,
        limit
    )

    return page


def get_item(
    item_id: str,
    collection_id: str,
    *,
    settings: ClientSettings,
    session: Session
) -> Item | None:

    return _get_item(
        settings.catalog_href,
        item_id,
        [collection_id],
        session=session,
        settings=settings
    )


def search_collections(
    walk_marker: Optional[WalkMarker] = None,
    limit: Optional[int] = 100,
    bbox: Optional[BBox] = None,
    datetime: Optional[Datetime] = None,
    filter: Optional[Union[str, Dict]] = None,
    *,
    settings: ClientSettings,
    session: Session
) -> WalkPage:

    walk_filter_chain = chain_walk_filters(
        make_walk_pagination_filter(
            start=walk_marker.start if walk_marker else None,
            end=walk_marker.end if walk_marker else None
        ),
        make_walk_spatial_extent_filter(
            geometry=bbox,
            assume_extent_spec=settings.assume_extent_spec
        ),
        make_walk_temporal_extent_filter(
            datetime,
            assume_extent_spec=settings.assume_extent_spec
        ),
        make_walk_collection_cql2_filter(filter)
    )

    filtered_walk = walk_filter_chain(
        walk_collections(
            settings.catalog_href,
            session=session,
            settings=settings
        )
    )

    page = WalkPage.paginate(
        filtered_walk,
        walk_marker,
        limit
    )

    return page


def get_collection(
    collection_id: str,
    *,
    settings: ClientSettings,
    session: Session
) -> Collection | None:
    return _get_collection(
        settings.catalog_href,
        collection_id=collection_id,
        session=session,
        settings=settings
    )


class CollectionNotFoundError(ValueError):
    ...


def search_collection_items(
    collection_id: str,
    bbox: Optional[BBox] = None,
    intersects: Optional[Intersection] = None,
    datetime: Optional[Datetime] = None,
    limit: int = 100,
    walk_marker: Optional[WalkMarker] = None,
    filter: Optional[Union[str, Dict]] = None,
    *,
    settings: ClientSettings,
    session: Session
) -> WalkPage:

    collection_walk_result = _get_collection(
        settings.catalog_href,
        collection_id=collection_id,
        session=session,
        settings=settings
    )

    if not collection_walk_result:
        raise CollectionNotFoundError(f"Collection {collection_id} not found.")

    walk_filter_chain = chain_walk_filters(
        make_walk_pagination_filter(
            start=walk_marker.start if walk_marker else None,
            end=walk_marker.end if walk_marker else None
        ),
        make_walk_filter_items(),
        make_walk_datetime_filter(
            datetime,
            assume_extent_spec=settings.assume_extent_spec
        ),
        make_walk_bbox_filter(
            bbox,
            assume_extent_spec=settings.assume_extent_spec
        ),
        make_walk_geometry_filter(
            intersects,
            assume_extent_spec=settings.assume_extent_spec
        ),
        make_walk_item_cql2_filter(filter)
    )

    filtered_walk = walk_filter_chain(walk(
        collection_walk_result,
        session=session,
        settings=settings
    ))

    page = WalkPage.paginate(
        filtered_walk,
        walk_marker,
        limit
    )

    return page
