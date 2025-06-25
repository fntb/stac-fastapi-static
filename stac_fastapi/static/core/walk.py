from __future__ import annotations

from typing import (
    Iterator,
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


def as_walk(walk_result_iterator: Iterator[WalkResult]) -> Iterator[WalkResult]:
    return chain_walks(walk_result_iterator)


def walk(
    root: str | WalkResult,
    *,
    session: requests.Session,
    settings: WalkSettings
) -> Iterator[WalkResult]:

    if not isinstance(root, WalkResult):
        root = WalkResult(
            href=root,
            walk_path=WalkPath(),
            type=Catalog,
            _session=session,
            _settings=settings
        )

    try:
        root.resolve()
    except BadWalkResultError as error:
        logger.warning(f"Skipping walk_result {str(root)} : {str(error)}", extra={
            "error": error
        })
        return

    walk_results = [
        WalkResult(
            href=href,
            walk_path=root.walk_path +
            WalkPath.encode(href),
            type=Item,
            _session=root._session,
            _settings=root._settings,
        )
        for href
        in get_item_hrefs(root.object)
    ] + [
        WalkResult(
            href=href,
            walk_path=root.walk_path +
            WalkPath.encode(href),
            type=(Collection, Catalog),
            _session=root._session,
            _settings=root._settings,
        )
        for href
        in get_child_hrefs(root.object)
    ]

    walk_results.sort(
        key=lambda link: link.walk_path
    )

    for walk_result in walk_results:
        try:
            yield walk_result
        except SkipWalk:
            yield None
            continue

        if walk_result.type == (Collection, Catalog) or walk_result.type in (Collection, Catalog):
            yield from walk(
                walk_result,
                session=session,
                settings=settings
            )
