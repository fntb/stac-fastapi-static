from typing import (
    Iterator,
    Callable,
    Optional
)

from stac_pydantic.collection import Collection
from stac_pydantic.item import Item
from stac_pydantic.catalog import Catalog

import requests
from .requests import Session

from .walk import (
    WalkResult,
    WalkSettings,
    as_walk,
    walk
)

from .walk_filter import (
    WalkFilter
)


def _get_collections_from_cache(
    collection_ids: Optional[list[str]] = None,
    *,
    session: requests.Session,
    settings: WalkSettings
):
    if not collection_ids:
        return None

    walk_results = [
        WalkResult.from_id(collection_id, session=session, settings=settings)
        for collection_id
        in collection_ids
    ]

    if not all(walk_results):
        return None

    return sorted(
        walk_results,
        key=lambda walk_result: walk_result.walk_path
    )


def make_filter_collections(collection_ids: Optional[list[str]] = None):
    def filter_collections(walk_result: WalkResult) -> WalkResult[Collection]:
        if walk_result.type == Item:
            return False

        walk_result.resolve()

        if not walk_result.type == Collection:
            return False

        if not collection_ids or walk_result.resolve_id() in collection_ids:
            return True

        return False

    return filter_collections


def walk_collections(
    root: str | WalkResult,
    collection_ids: Optional[list[str]] = None,
    *,
    session: requests.Session,
    settings: WalkSettings
) -> Iterator[WalkResult[Collection]]:

    if (cached_walk_results := _get_collections_from_cache(
        collection_ids=collection_ids,
        session=session,
        settings=settings
    )) is not None:
        return as_walk(cached_walk_results)
    else:
        return WalkFilter(
            walk(
                root=root,
                session=session,
                settings=settings
            ),
            make_filter_collections(collection_ids)
        )


def get_collection(
    root: str | WalkResult,
    collection_id: str,
    *,
    session: requests.Session,
    settings: WalkSettings
) -> WalkResult[Collection] | None:
    return next(
        walk_collections(
            root,
            collection_ids=[collection_id],
            session=session,
            settings=settings
        ),
        None
    )
