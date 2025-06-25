
from typing import (
    Iterator,
    Optional
)

from stac_pydantic.collection import Collection
from stac_pydantic.item import Item
from stac_pydantic.catalog import Catalog

import requests

from .walk import (
    WalkResult,
    chain_walks,
    WalkSettings,
    as_walk,
    walk
)

from .walk_filter import (
    WalkFilter
)


from .walk_collections import (
    walk_collections
)


def make_filter_items(item_ids: Optional[list[str]] = None):
    def filter_items(walk_result: WalkResult) -> WalkResult[Item]:
        if walk_result.type == Item:
            if not item_ids:
                return walk_result
            elif walk_result.resolve_id() in item_ids:
                return walk_result

    return filter_items


def _get_items_from_cache(
    item_ids: Optional[list[str]] = None,
    collection_ids: Optional[list[str]] = None,
    *,
    session: requests.Session,
    settings: WalkSettings
):
    if not item_ids:
        return None

    walk_results = [
        WalkResult.from_id(item_id, session=session, settings=settings)
        for item_id
        in item_ids
    ]

    if not all(walk_results):
        return None

    if collection_ids:
        collection_walk_results = [
            WalkResult.from_id(collection_id, session=session, settings=settings)
            for collection_id
            in collection_ids
        ]

        if not all(collection_walk_results):
            return None

        walk_results = [
            walk_result
            for walk_result
            in walk_results
            if any(
                walk_result.walk_path in collection_walk_result.walk_path
                for collection_walk_result
                in collection_walk_results
            )
        ]

    return sorted(
        walk_results,
        key=lambda walk_result: walk_result.walk_path
    )


def walk_items(
    root: str | WalkResult,
    item_ids: Optional[list[str]] = None,
    collection_ids: Optional[list[str]] = None,
    *,
    session: requests.Session,
    settings: WalkSettings,
) -> Iterator[WalkResult[Item]]:

    if (cached_walk_results := _get_items_from_cache(
            item_ids=item_ids,
            collection_ids=collection_ids,
            session=session,
            settings=settings
    )) is not None:
        return as_walk(cached_walk_results)
    else:
        return WalkFilter(
            chain_walks(
                *(
                    walk(
                        collection,
                        session=session,
                        settings=settings
                    )
                    for collection
                    in walk_collections(
                        root,
                        collection_ids=collection_ids,
                        session=session,
                        settings=settings
                    )
                )
            ) if collection_ids else walk(
                root,
                session=session,
                settings=settings,
            ),
            make_filter_items(item_ids)
        )


def get_item(
    root: str | WalkResult,
    item_id: str,
    collection_ids: Optional[list[str]] = None,
    *,
    session: requests.Session,
    settings: WalkSettings,
) -> WalkResult[Collection] | None:
    return next(
        walk_items(
            root,
            item_ids=[item_id],
            collection_ids=collection_ids,
            session=session,
            settings=settings
        ),
        None
    )
