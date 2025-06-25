from __future__ import annotations

from typing import (
    Callable,
    TypeVar,
    Any,
    Generator,
    Optional,
    Type,
    Generic,
    List,
    Iterator
)

from dataclasses import dataclass
import dataclasses

import time
import math

from .walk import (
    WalkResult,
    BadWalkResultError,
    SkipWalk,
    logger,
)

from stac_pydantic.collection import Collection
from stac_pydantic.item import Item
from stac_pydantic.catalog import Catalog


T = TypeVar("T", Catalog, Collection, Item)


@dataclass(kw_only=True)
class WalkFilterStats():
    name: str

    items: int = 0
    collections: int = 0

    items_errored: int = 0
    items_matched: int = 0

    collections_errored: int = 0
    collections_matched: int = 0

    _items_time: float = 0
    _items_resolution_time: float = 0
    _collections_time: float = 0
    _collections_resolution_time: float = 0

    @property
    def time_per_item(self) -> float:
        return (self._items_time / self.items) if self.items else 0

    @property
    def resolution_time_per_item(self) -> float:
        return (self._items_resolution_time / self.items) if self.items else 0

    @property
    def time_per_collection(self) -> float:
        return (self._collections_time / self.collections) if self.collections else 0

    @property
    def resolution_time_per_collection(self) -> float:
        return (self._collections_resolution_time / self.collections) if self.collections else 0

    def report(
        self,
        walk_result: WalkResult,
        filter_result: bool,
        *,
        time: float,
        resolution_time: Optional[float] = None,
        error: Optional[Exception] = None,
    ):
        if walk_result.type == Item:
            self.items += 1
            self._items_time += time
            self._items_resolution_time += resolution_time

            if filter_result == True:
                self.items_matched += 1

            if error is not None:
                self.items_errored += 1
        else:
            self.collections += 1
            self._collections_time += time
            self._collections_resolution_time += resolution_time

            if filter_result == True:
                self.collections_matched += 1

            if error is not None:
                self.collections_errored += 1

    def asdict(self):
        return {
            **dataclasses.asdict(self),
            "time_per_item": self.time_per_item,
            "resolution_time_per_item": self.resolution_time_per_item,
            "time_per_collection": self.time_per_collection,
            "resolution_time_per_collection": self.resolution_time_per_collection
        }

    def __str__(self):
        def time_to_str(t: float):
            return (str(math.ceil(t * 10) / 10) if t >= 0.1 else "<0.1") + "ms"

        time_per_item_str = time_to_str(self.time_per_item)
        time_per_collection_str = time_to_str(self.time_per_collection)

        time_per_item_resolution_str = f"({time_to_str(self.resolution_time_per_item)})" if self.resolution_time_per_item else ""
        time_per_collection_resolution_str = f"({time_to_str(self.resolution_time_per_collection)})" if self.resolution_time_per_collection else ""

        items_errored_str = f"(-{self.items_errored})" if self.items_errored else ""
        collections_errored_str = f"(-{self.collections_errored})" if self.collections_errored else ""

        return (
            f"{self.name}:"
            f" items[{self.items_matched}{items_errored_str}/{self.items},{time_per_item_str}{time_per_item_resolution_str}]"
            f" collections[{self.collections_matched}{collections_errored_str}/{self.collections},{time_per_collection_str}{time_per_collection_resolution_str}]"
        )


class WalkFilter(Generator[WalkResult[T], None, None], Generic[T]):

    _walk: WalkFilter | Iterator[WalkResult]
    _filter: Callable[[WalkResult], Optional[bool | WalkResult[T]]]
    _current_yielded_walk_result: T | None = None

    stats: WalkFilterStats

    @classmethod
    def build_chain(
        cls,
        *filters: Callable[[WalkResult], Optional[bool | WalkResult]] | None
    ):
        def make_filter_chain(
            walk: Iterator[WalkResult] | WalkFilter
        ) -> Iterator[WalkResult] | WalkFilter:
            filtered_walk = walk

            for filter in filters:
                if filter is not None:
                    filtered_walk = cls(filtered_walk, filter)

            return filtered_walk

        return make_filter_chain

    def __init__(self, walk: WalkFilter | Iterator[WalkResult], filter: Callable[[WalkResult], Optional[bool | WalkResult[T]]]):
        self._walk = walk
        self._filter = filter
        self.stats = WalkFilterStats(
            name=filter.__name__
        )

    def _skip_walk(self, error: SkipWalk):
        none = self._walk.throw(error)

        if none is not None:
            logger.error(f"Exception propagation yielded a walk result, it will be silently swallowed and inconsistencies will arise. This error is probably due to an incompatible walk filter implementation.", extra={
                "walk_result": none
            })

        return none

    def _prepare_report(self, walk_result: WalkResult):
        t_start = time.time()
        was_resolved = walk_result.is_resolved()

        def report(result: bool, error: Optional[Exception] = None):
            is_resolved = walk_result.is_resolved()
            t_end = time.time()
            dt = (t_end - t_start) * 1000
            dt_resolution = walk_result.resolution_time if (not was_resolved and is_resolved) else 0

            self.stats.report(
                walk_result,
                filter_result=result,
                time=dt,
                resolution_time=dt_resolution,
                error=error
            )

        return report

    def __next__(self) -> WalkResult[T]:
        while True:
            current_walk_result = next(self._walk)
            report = self._prepare_report(current_walk_result)

            try:
                filtered_current_walk_result = self._filter(current_walk_result)

                if filtered_current_walk_result in [False, None]:
                    self._current_yielded_walk_result = None
                    report(False)
                elif filtered_current_walk_result == True:
                    self._current_yielded_walk_result = current_walk_result
                    report(True)
                else:
                    self._current_yielded_walk_result = filtered_current_walk_result
                    report(True)
            except BadWalkResultError as error:
                logger.warning(f"Skipping walk_result {str(current_walk_result)} : {str(error)}", extra={
                    "error": error
                })

                report(False, error=error)
                continue
            except SkipWalk as error:
                self._current_yielded_walk_result = self._skip_walk(error)

                report(False)
                continue
            else:
                if self._current_yielded_walk_result is not None:
                    return self._current_yielded_walk_result
                else:
                    continue

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

        if isinstance(typ, SkipWalk):
            self._skip_walk(typ)
        elif safe_issubclass(typ, SkipWalk):
            self._skip_walk(value or typ)
        else:
            return super().throw(typ, value, traceback)

    @property
    def chain_stats(self) -> List[WalkFilterStats]:
        if isinstance(self._walk, WalkFilter):
            return self._walk.chain_stats + [self.stats]
        else:
            return [self.stats]
