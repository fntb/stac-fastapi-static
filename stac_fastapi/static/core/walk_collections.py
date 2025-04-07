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
    walk,
    WalkResult,
    SkipWalk,
    WalkSettings
)

from .walk_filters import (
    make_walk_filter,
    backraise_skip_walk
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
        for walk_result in cached_walk_results:
            try:
                yield walk_result
            except SkipWalk:
                yield None

                continue
    else:

        def filter_collections(walk_result: WalkResult):
            if walk_result.type is Item:
                return False

            walk_result.resolve()

            if not walk_result.type is Collection:
                return False

            if not collection_ids or walk_result.resolve_id() in collection_ids:
                return True

            return False

        for walk_result in (_walk := make_walk_filter(filter_collections)(
            walk(
                root,
                session=session,
                settings=settings,
            )
        )):
            try:
                yield walk_result
            except SkipWalk:
                yield None

                backraise_skip_walk(_walk)


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
