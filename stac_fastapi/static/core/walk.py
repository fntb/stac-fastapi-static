from __future__ import annotations

from typing import (
    Iterator
)

import logging

from stac_pydantic.collection import Collection
from stac_pydantic.item import Item
from stac_pydantic.catalog import Catalog

import requests

from .walk_path import WalkPath
from .walk_result import (
    WalkResult,
    BadWalkResultError,
    WalkSettings
)

from .model import (
    get_child_hrefs,
    get_item_hrefs,
)

logger = logging.getLogger(__name__)


class SkipWalk(StopIteration):
    pass


def chain_walks(*walks: Iterator[WalkResult]) -> Iterator[WalkResult]:
    for walk in walks:
        for walk_result in walk:
            try:
                yield walk_result
            except SkipWalk:
                yield None
                continue


def walk(
    root: str | WalkResult,
    *,
    session: requests.Session,
    settings: WalkSettings
) -> Iterator[WalkResult]:

    if not isinstance(root, WalkResult):
        root_result = WalkResult(
            href=root,
            walk_path=WalkPath(),
            type=Catalog,
            _session=session,
            _settings=settings
        )
    else:
        root_result = root

    try:
        root_result.resolve()
    except BadWalkResultError as error:
        logger.warning(f"Skipping walk_result {str(root_result)} : {str(error)}", extra={
            "error": error
        })
        return

    walkable_links = [
        WalkResult(
            href=href,
            walk_path=root_result.walk_path +
            WalkPath.encode(href),
            type=Item,
            _session=root_result._session,
            _settings=root_result._settings,
        )
        for href
        in get_item_hrefs(root_result.object)
    ] + [
        WalkResult(
            href=href,
            walk_path=root_result.walk_path +
            WalkPath.encode(href),
            type=Catalog,
            _session=root_result._session,
            _settings=root_result._settings,
        )
        for href
        in get_child_hrefs(root_result.object)
    ]

    walkable_links.sort(
        key=lambda link: link.walk_path
    )

    for walkable_link in walkable_links:

        try:
            yield walkable_link
        except SkipWalk:
            yield None
            continue

        if walkable_link.type is not Item:
            yield from walk(
                walkable_link,
                session=session,
                settings=settings
            )
