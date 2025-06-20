from __future__ import annotations
from collections import (
    deque
)

from typing import (
    Iterator,
    List,
    Any,
    Type,
    Optional,
    Callable,
    Generator
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
) -> Walk:

    return Walk(
        root=root,
        session=session,
        settings=settings
    )


class Walk(Generator):

    root: WalkResult

    _remaining_walk_results: deque[WalkResult]
    _current_yielding_walk: Walk | None = None
    _current_yielded_walk_result: WalkResult | None = None

    def __init__(
        self,
        root: str | WalkResult,
        *,
        session: requests.Session,
        settings: WalkSettings
    ):

        if not isinstance(root, WalkResult):
            root = WalkResult(
                href=root,
                walk_path=WalkPath(),
                type=Catalog,
                _session=session,
                _settings=settings
            )

        self.root = root

        try:
            root.resolve()
        except BadWalkResultError as error:
            logger.warning(f"Skipping walk_result {str(root)} : {str(error)}", extra={"error": error})

            self._remaining_walk_results = deque()
        else:
            walk_results = [
                WalkResult(
                    href=href,
                    walk_path=root.walk_path + WalkPath.encode(href),
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
                    type=Catalog,
                    _session=root._session,
                    _settings=root._settings,
                )
                for href
                in get_child_hrefs(root.object)
            ]

            walk_results.sort(
                key=lambda walk_result: walk_result.walk_path
            )

            self._remaining_walk_results = deque(walk_results)

    def __next__(self) -> WalkResult:
        if self._current_yielding_walk:
            try:
                self._current_yielded_walk_result = next(self._current_yielding_walk)
                return self._current_yielded_walk_result
            except StopIteration:
                self._current_yielding_walk = None

        if not self._remaining_walk_results:
            self._current_yielded_walk_result = None
            raise StopIteration

        walk_result = self._remaining_walk_results.popleft()

        self._current_yielded_walk_result = walk_result

        if walk_result.type is not Item:
            self._current_yielding_walk = Walk(
                walk_result,
                session=walk_result._session,
                settings=walk_result._settings
            )

        return self._current_yielded_walk_result

    def __iter__(self):
        return self

    def send(self, value: Any = None):
        return super().send(value)

    def throw(self, typ: Type[Exception], value: Exception = None, traceback: Any = None):
        def safe_issubclass(typ, cls):
            try:
                return issubclass(typ, cls)
            except TypeError:
                return False

        if safe_issubclass(typ, SkipWalk) or isinstance(typ, SkipWalk):
            self._current_yielding_walk = None
        else:
            return super().throw(typ, value, traceback)
