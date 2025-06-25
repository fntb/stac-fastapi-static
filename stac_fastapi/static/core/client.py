from typing import (
    Optional,
    List,
    Union,
    Tuple,
    Dict,
    Callable,
    Iterator
)

from typing_extensions import (
    Self
)

import datetime as datetimelib
import time
import math

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
    walk,
    logger,
    WalkResult,
)

from .walk_items import (
    walk_items,
    get_item as _get_item,
    make_filter_items
)

from .walk_collections import (
    walk_collections,
    get_collection as _get_collection
)

from .pagination import (
    WalkMarker,
    WalkPage
)

from .walk_filter import (
    WalkFilter
)

from .filter_page import (
    make_filter_page
)
from .filter_cql2 import (
    make_filter_collections_cql2,
    make_filter_items_cql2
)
from .filter_depth import (
    make_filter_depth
)
from .filter_temporal_extent import (
    make_filter_collections_temporal_extent,
    make_filter_items_temporal_extent
)
from .filter_spatial_extent import (
    make_filter_collections_spatial_extent,
    make_filter_items_spatial_extent
)


class ClientSettings(WalkSettings):
    catalog_href: str
    log_level: str


Datetime = Union[
    datetimelib.datetime,
    Tuple[datetimelib.datetime, datetimelib.datetime],
    Tuple[datetimelib.datetime, None],
    Tuple[None, datetimelib.datetime],
]


def walk_page(
    walk: Iterator[WalkResult] | WalkFilter,
    walk_marker: Optional[WalkMarker] = None,
    limit: Optional[int] = 10
) -> WalkPage:
    t_start = time.time()
    page = WalkPage.paginate(
        walk,
        walk_marker,
        limit
    )
    dt = (time.time() - t_start) * 1000

    if isinstance(walk, WalkFilter) and dt >= 250:
        logger.warning(
            f"Slow response time : {math.ceil(dt)}ms : " +
            " ~ ".join([str(stats) for stats in walk.chain_stats])
        )

    return page


def search_items(
    collections: Optional[List[str]] = None,
    ids: Optional[List[str]] = None,
    bbox: Optional[BBox] = None,
    intersects: Optional[Intersection] = None,
    datetime: Optional[Datetime] = None,
    walk_marker: Optional[WalkMarker] = None,
    limit: Optional[int] = 10,
    filter: Optional[Union[str, Dict]] = None,
    *,
    settings: ClientSettings,
    session: Session
) -> WalkPage:

    if ids:
        walk_filter_chain = WalkFilter.build_chain(
            make_filter_page(
                start=walk_marker.start,
                end=walk_marker.end
            ) if walk_marker is not None else None
        )

        _walk = walk_items(
            settings.catalog_href,
            item_ids=ids,
            collection_ids=collections,
            session=session,
            settings=settings
        )
    else:
        walk_filter_chain = WalkFilter.build_chain(
            make_filter_page(
                start=walk_marker.start,
                end=walk_marker.end
            ) if walk_marker is not None else None,
            make_filter_collections_spatial_extent(
                bbox=bbox,
                geometry=intersects,
            ) if bbox is not None or intersects is not None else None,
            make_filter_collections_temporal_extent(
                datetime,
            ) if datetime is not None and datetime != (None, None) else None,
            make_filter_items(),
            make_filter_items_temporal_extent(
                datetime,
            ) if datetime is not None and datetime != (None, None) else None,
            make_filter_items_spatial_extent(
                bbox=bbox,
                geometry=intersects
            ) if bbox is not None or intersects is not None else None,
            make_filter_items_cql2(filter) if filter is not None else None
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

    _walk = walk_filter_chain(_walk)

    return walk_page(
        _walk,
        walk_marker,
        limit
    )


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
    limit: Optional[int] = 10,
    bbox: Optional[BBox] = None,
    datetime: Optional[Datetime] = None,
    filter: Optional[Union[str, Dict]] = None,
    *,
    settings: ClientSettings,
    session: Session
) -> WalkPage:
    _walk = WalkFilter.build_chain(
        make_filter_page(
            start=walk_marker.start,
            end=walk_marker.end
        ) if walk_marker is not None else None,
        make_filter_collections_spatial_extent(
            bbox=bbox,
        ) if bbox is not None else None,
        make_filter_collections_temporal_extent(
            datetime,
        ) if datetime is not None and datetime != (None, None) else None,
        make_filter_collections_cql2(
            filter
        ) if filter is not None else None
    )(
        walk_collections(
            settings.catalog_href,
            session=session,
            settings=settings
        )
    )

    return walk_page(
        _walk,
        walk_marker,
        limit
    )


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
    limit: int = 10,
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

    _walk = WalkFilter.build_chain(
        make_filter_page(
            start=walk_marker.start,
            end=walk_marker.end
        ) if walk_marker is not None else None,
        make_filter_items(),
        make_filter_items_temporal_extent(datetime) if datetime is not None and datetime != (None, None) else None,
        make_filter_items_spatial_extent(
            bbox=bbox,
            geometry=intersects
        ) if bbox is not None or intersects is not None else None,
        make_filter_items_cql2(filter) if filter is not None else None
    )(
        walk(
            collection_walk_result,
            session=session,
            settings=settings
        )
    )

    return walk_page(
        _walk,
        walk_marker,
        limit
    )
