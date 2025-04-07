from __future__ import annotations
from typing import (
    Iterator,
    Callable,
    Optional,
    Generator,
    overload,
    TypeVar,
    Generic
)
from collections import (
    deque
)
import json
import datetime as datetimelib
import random
import os
from os import path
import shutil

import shapely
import pystac
import pystac.layout
from stac_pydantic.shared import BBox

from ..stac_generator import generate_catalog
from ..compat import fromisoformat
from .get_items import (
    get_items,
)
from .get_collections import (
    get_collections,
)

T = TypeVar("T")
R = TypeVar("R")


class ResultGenerator(Generic[T, R]):

    _generator: Generator[T, None, R]
    _result: R
    _consumed: bool = False

    def __init__(self, generator: Generator[T, None, R]):
        self._generator = generator

    def __iter__(self) -> Generator[T, None, R]:
        self._result = yield from self._generator
        self._consumed = True
        return self._result

    @property
    def result(self) -> R:
        if not self._consumed:
            deque(self, maxlen=0)

        return self._result


U = TypeVar("U")


def optimized_sample(it: Iterator[Generic[U]], k: int = 1):
    # TODO : Recursive dicotomy
    return random.sample(list(it), k=k)


def pick_random_walk(catalog: pystac.STACObject, root: Optional[pystac.Catalog]) -> list[pystac.STACObject]:
    if isinstance(catalog, pystac.Item):
        return [catalog]

    child_links = [
        link
        for link
        in catalog.links
        if link.rel == pystac.RelType.CHILD
    ]

    if child_links:
        child_link = random.choice(child_links)
        child_link.resolve_stac_object(root)
        child = child_link.target
        return [catalog, *pick_random_walk(child, root)]

    item_links = [
        link
        for link
        in catalog.links
        if link.rel == pystac.RelType.ITEM
    ]

    if item_links:
        item_link = random.choice(item_links)
        item_link.resolve_stac_object(root)
        item = item_link.target
        return [catalog, item]

    return [catalog]


class TestCatalog():
    __test__ = False

    catalog_href: str
    catalog: pystac.Catalog

    @overload
    @classmethod
    def generate(
        cls,
        catalog_href: str | None = None,
        n_items: int = 1000,
        track_progress: False = False
    ) -> TestCatalog:
        ...

    @overload
    @classmethod
    def generate(
        cls,
        catalog_href: str | None = None,
        n_items: int = 1000,
        track_progress: True = True
    ) -> ResultGenerator[pystac.STACObject, TestCatalog]:
        ...

    @classmethod
    def _generate(
        cls,
        catalog_href: str | None = None,
        n_items: int = 1000,
    ) -> Generator[pystac.STACObject, None, TestCatalog]:
        if not catalog_href:
            catalog_href = path.abspath(path.join("stac_test_catalogs", str(n_items), "catalog.json"))

        if path.exists(catalog_href):
            return cls(catalog_href)

        dir = path.dirname(catalog_href)

        catalog = yield from generate_catalog(n_items)

        try:
            os.makedirs(dir)

            catalog.normalize_hrefs(
                catalog_href,
                strategy=pystac.layout.BestPracticesLayoutStrategy()
            )

            catalog.save(
                catalog_type=pystac.CatalogType.SELF_CONTAINED
            )

        except Exception as error:
            shutil.rmtree(dir, ignore_errors=True)
            raise error

        return cls(catalog_href)

    @classmethod
    def generate(
        cls,
        catalog_href: str | None = None,
        n_items: int = 1000,
        track_progress: bool = True
    ) -> ResultGenerator[pystac.STACObject, TestCatalog] | TestCatalog:  # type: ignore

        generator = ResultGenerator(cls._generate(
            catalog_href=catalog_href,
            n_items=n_items
        ))

        if track_progress:
            return generator
        else:
            return generator.result

    def __init__(self, catalog_href: str):
        self.catalog_href = catalog_href
        self.catalog = pystac.Catalog.from_file(catalog_href)

    @property
    def collections(self) -> Iterator[pystac.Collection]:
        yield from get_collections(self.catalog)

    @property
    def items(self) -> Iterator[pystac.Item]:
        yield from get_items(self.catalog)

    def get_collection(self, id: str) -> pystac.Collection | None:
        for collection in self.collections:
            if collection.id == id:
                return collection

    def pick_collections(self, n: int = 1, use_heuristic: bool = True) -> list[pystac.Collection]:
        if not use_heuristic:
            return optimized_sample(self.collections, k=n)
        else:
            sample = []

            while len(sample) < n:
                random_walk = pick_random_walk(self.catalog, root=self.catalog)
                sample.append(
                    random.choice(
                        list(
                            object
                            for object
                            in random_walk
                            if isinstance(object, pystac.Collection)
                        )
                    )
                )

            return sample

    def pick_collection(self, use_heuristic: bool = True) -> pystac.Collection:
        return self.pick_collections(use_heuristic=use_heuristic).pop()

    def get_item(self, id: str) -> pystac.Item | None:
        for item in self.items:
            if item.id == id:
                return item

    def pick_items(self, n: int = 1, collection: Optional[pystac.Collection] = None, use_heuristic: bool = True) -> list[pystac.Item]:
        if use_heuristic:
            collection = collection or self.catalog
            sample = []

            while len(sample) < n:
                random_object = pick_random_walk(collection, root=self.catalog).pop()
                if isinstance(random_object, pystac.Item):
                    sample.append(random_object)

            return sample
        elif collection:
            return optimized_sample(get_items(collection), k=n)
        else:
            return optimized_sample(self.items, k=n)

    def pick_item(self, collection: Optional[pystac.Collection] = None, use_heuristic: bool = True) -> pystac.Item:
        return self.pick_items(collection=collection, use_heuristic=use_heuristic).pop()

    def pick_walk(self, use_heuristic: bool = True) -> list[pystac.STACObject]:
        if use_heuristic:
            return pick_random_walk(self.catalog, root=self.catalog)
        else:
            stac_object = self.pick_item(use_heuristic=False)
            walk = [stac_object]

            while stac_object.get_parent():
                walk.append(stac_object := stac_object.get_parent())

            return list(reversed(walk))

    def pick_geometry(self, use_heuristic: bool = True) -> shapely.Geometry:
        items = self.pick_items(2, use_heuristic=use_heuristic)
        geometries = [shapely.from_geojson(json.dumps(item.geometry)) for item in items]
        envelope = shapely.envelope(shapely.GeometryCollection(geometries))

        return envelope

    def pick_datetime_intervals(self, use_heuristic: bool = True) -> list[tuple[datetimelib.datetime | None, datetimelib.datetime | None]]:
        items = self.pick_items(2, use_heuristic=use_heuristic)

        start_datetime = min(
            fromisoformat(
                item.properties.get(
                    "start_datetime", item.datetime and item.datetime.isoformat()
                )
            )
            for item
            in items
        )

        end_datetime = max(
            fromisoformat(
                item.properties.get(
                    "end_datetime", item.datetime and item.datetime.isoformat()
                )
            )
            for item
            in items
        )

        return [
            (None, None),
            (start_datetime, None),
            (None, end_datetime),
            (start_datetime, end_datetime),
            (start_datetime, start_datetime)
        ]

    def pick_datetime_interval(self, use_heuristic: bool = True) -> tuple[datetimelib.datetime | None, datetimelib.datetime | None]:
        return self.pick_datetime_intervals(use_heuristic=use_heuristic)[random.randint(0, 4)]

    def pick_bbox(self, use_heuristic: bool = True) -> BBox:
        items = self.pick_items(2, use_heuristic=use_heuristic)
        bboxes = [shapely.box(*item.bbox) for item in items]
        envelope: shapely.Polygon = shapely.envelope(
            shapely.GeometryCollection(bboxes))

        return envelope.bounds
