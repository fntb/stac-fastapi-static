from __future__ import annotations

from typing import (
    Callable,
    TypeVar,
    Any,
    Generator,
    Optional,
    Type,
    Generic,
    List
)

from typing_extensions import (
    Self
)

from .walk import (
    WalkResult,
    BadWalkResultError,
    SkipWalk,
    Walk,
    logger as walk_logger
)

from stac_pydantic.collection import Collection
from stac_pydantic.item import Item
from stac_pydantic.catalog import Catalog


T = TypeVar("T", Catalog, Collection, Item)
S = TypeVar("S", Catalog, Collection, Item)


class WalkFilterChainBuilder():

    _filters: List[Callable[[WalkResult], Optional[bool | WalkResult[T]]]]

    def __init__(self):
        self._filters = []

    def chain(self, filter: Callable[[WalkResult], Optional[bool | WalkResult[T]]]) -> Self:
        self._filters.append(filter)

        return self

    def make(self, walk: Walk | WalkFilter) -> WalkFilter:
        filtered_walk = walk

        for filter in self._filters:
            filtered_walk = WalkFilter(filtered_walk, filter)

        return filtered_walk


class WalkFilter(Generator, Generic[T]):

    _walk: Walk
    _filter: Callable[[WalkResult], Optional[bool | WalkResult[T]]]
    _current_yielded_walk_result: T | None = None

    def __init__(self, walk: Walk | WalkFilter, filter: Callable[[WalkResult], Optional[bool | WalkResult[T]]]):
        self._walk = walk
        self._filter = filter

    def _propagate_skip_walk(self, error: SkipWalk):
        none = self._walk.throw(error)

        if none is not None:
            walk_logger.error(f"Exception descent yielded a walk result, it will be silently swallowed and inconsistencies will arise. This error is probably due to an incompatible walk filter implementation.", extra={
                "walk_result": none
            })

        assert none == None

        return none

    def __next__(self) -> WalkResult[T]:
        current_walk_result = next(self._walk)

        try:
            filtered_current_walk_result = self._filter(current_walk_result)

            if filtered_current_walk_result in [False, None]:
                self._current_yielded_walk_result = None
            elif filtered_current_walk_result == True:
                self._current_yielded_walk_result = current_walk_result
            else:
                self._current_yielded_walk_result = filtered_current_walk_result
        except BadWalkResultError as error:
            walk_logger.warning(f"Skipping walk_result {str(current_walk_result)} : {str(error)}", extra={
                "error": error
            })

            return next(self)
        except SkipWalk as error:
            self._current_yielded_walk_result = self._propagate_skip_walk(error)

            return next(self)
        else:
            if self._current_yielded_walk_result is not None:
                return self._current_yielded_walk_result
            else:
                return next(self)

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
            self._propagate_skip_walk(typ)
        elif safe_issubclass(typ, SkipWalk):
            self._propagate_skip_walk(value or typ)
        else:
            return super().throw(typ, value, traceback)
