from __future__ import annotations

from typing import (
    Optional,
    Type,
    ClassVar,
    NamedTuple,
    TypeVar,
    Generic,
    Tuple
)

import dataclasses
import time
import http


from stac_pydantic.collection import Collection
from stac_pydantic.item import Item
from stac_pydantic.catalog import Catalog

import requests

from .lib.tiered_cache import TieredCache

from .requests import Session

from .fetch import (
    fetch_walkable,
    fetch_item,
    fetch_id,
    HTTPError,
)

from .errors import (
    BadStacObjectError
)

from .walk_path import WalkPath


class WalkSettings:
    assume_absolute_hrefs: bool
    assume_best_practice_layout: bool


class CachedWalkResult(NamedTuple):
    href: str
    walk_path: WalkPath
    type: Catalog | Collection | Item
    id: str


class WalkResultCache(TieredCache[CachedWalkResult]):

    def set(self, id: str, walk_result: WalkResult):
        key = id
        value = CachedWalkResult(
            href=walk_result.href,
            walk_path=walk_result.walk_path,
            type=walk_result.type,
            id=id
        )
        priority = -1 if walk_result.type == Item else 0

        super().set(key, value, priority)

    def get(self, id: str) -> CachedWalkResult | None:
        return super().get(id, (-1, 0))

    def delete(self, id: str):
        return super().delete(id, (-1, 0))


class BadWalkResultError(Exception):
    ...


T = TypeVar("T", Catalog, Collection, Item)


@dataclasses.dataclass(order=True)
class WalkResult(Generic[T]):
    _cache: ClassVar[WalkResultCache] = WalkResultCache()
    _session: Session
    _settings: WalkSettings

    href: str
    walk_path: WalkPath

    type: Type[T | Tuple[T]]
    object: Optional[T] = None

    _resolution_time: Optional[float] = None

    def __post_init__(self):
        if self.is_resolved():
            self._cache.set(id, self)

    def __str__(self):
        typ = (typ.__name__ for typ in self.type) if isinstance(self.type, Tuple) else self.type.__name__

        return f"WalkResult(type={typ}, href={self.href}, walk_path={str(self.walk_path)})"

    def is_resolved(self):
        return self.object is not None

    @property
    def resolution_time(self):
        return self._resolution_time

    def resolve(
        self,
        *,
        force: bool = False,
    ) -> T:
        if self.is_resolved() and not force:
            return self.object

        t_start = time.time()
        if self.type == Item:
            try:
                self.object = fetch_item(
                    self.href,
                    session=self._session,
                    assume_absolute_hrefs=self._settings.assume_absolute_hrefs
                )
                self.type = Item
            except HTTPError as error:
                raise BadWalkResultError(
                    f"Network Error : {self.href} : {error.response.status_code} - {http.HTTPStatus(error.response.status_code).phrase}") from error
            except BadStacObjectError as error:
                raise BadWalkResultError(str(error)) from error
        else:
            try:
                self.object = fetch_walkable(
                    self.href,
                    session=self._session,
                    assume_absolute_hrefs=self._settings.assume_absolute_hrefs
                )
                self.type = type(self.object)
            except HTTPError as error:
                raise BadWalkResultError(
                    f"Network Error : {self.href} : {error.response.status_code} - {http.HTTPStatus(error.response.status_code).phrase}") from error
            except BadStacObjectError as error:
                raise BadWalkResultError(str(error)) from error

        self._cache.set(self.object.id, self)
        self._resolution_time = (time.time() - t_start) * 1000

        return self.object

    def resolve_id(
        self,
        *,
        force: bool = False
    ) -> str:
        if self.is_resolved() and not force:
            return self.object.id

        if self.type == Item:
            try:
                id = fetch_id(
                    self.href,
                    session=self._session,
                    assume_best_practice_layout=self._settings.assume_best_practice_layout
                )
            except HTTPError as error:
                raise BadWalkResultError(
                    f"Network Error : {self.href} : {error.response.status_code} - {http.HTTPStatus(error.response.status_code).phrase}") from error
            except BadStacObjectError as error:
                raise BadWalkResultError(str(error)) from error

            self._cache.set(id, self)
        else:
            id = self.resolve().id

        return id

    @classmethod
    def from_id(
        cls,
        id: str,
        *,
        session: requests.Session,
        settings: WalkSettings
    ) -> WalkResult | None:
        cached_walk_result = cls._cache.get(id)

        if not cached_walk_result:
            return None

        walk_result = WalkResult(
            href=cached_walk_result.href,
            walk_path=cached_walk_result.walk_path,
            type=cached_walk_result.type,
            _session=session,
            _settings=settings
        )

        if walk_result.resolve_id(force=True) != id:
            cls._cache.delete(id)

            return None

        return walk_result
