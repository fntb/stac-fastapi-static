from typing import (
    Optional
)

import math
import logging
import datetime as datetimelib
import random

import pytest
import pystac
import shapely

from stac_pydantic.item import Item
from stac_pydantic.collection import Collection
from stac_pydantic.shared import BBox
from geojson_pydantic.geometries import Geometry

from ..conftest import (
    TestCatalog,
    get_items
)

from stac_test_tools import (
    generate_item
)

from stac_fastapi.static.core import (
    walk,
    make_walk_pagination_filter,
    make_walk_datetime_filter,
    make_walk_temporal_extent_filter,
    make_walk_item_cql2_filter,
    walk_collections,
    walk_items
)

from stac_fastapi.static.api import (
    Settings
)

from stac_fastapi.static.core.walk_filters.temporal_filters import (
    make_match_datetime,
    make_match_temporal_extent
)
from stac_fastapi.static.core.walk_filters.spatial_filters import (
    make_match_geometry,
    make_match_bbox
)
from stac_fastapi.static.core.walk_filters.cql2_filter import (
    make_match_item_cql2
)


from stac_fastapi.static.core.requests import FileSession
from stac_fastapi.static.core.requests import file_path_to_file_uri


class TestWalk():

    session = FileSession()
    settings: Settings
    test_catalog: TestCatalog

    @staticmethod
    def _cast_item(item: pystac.Item) -> Item:
        return Item.model_validate(item.to_dict(include_self_link=False))

    @staticmethod
    def _cast_collection(collection: pystac.Collection) -> Collection:
        return Collection.model_validate(collection.to_dict(include_self_link=False))

    @pytest.fixture(autouse=True)
    def _init_test_catalog(self, test_catalog):
        self.test_catalog = test_catalog
        self.settings = Settings(
            catalog_href=file_path_to_file_uri(self.test_catalog.catalog_href)
        )

    def test_walk_everything(self):
        hrefs = set(
            file_path_to_file_uri(object.get_self_href())
            for object
            in self.test_catalog.collections
        )
        hrefs |= set(
            file_path_to_file_uri(object.get_self_href())
            for object
            in self.test_catalog.items
        )

        walked_hrefs = set(
            link.href
            for link
            in walk(file_path_to_file_uri(self.test_catalog.catalog_href), session=self.session, settings=self.settings)
        )

        assert hrefs == walked_hrefs

    def test_walk_order(self):
        walked_paths = [
            link.walk_path
            for link
            in walk(file_path_to_file_uri(self.test_catalog.catalog_href), session=self.session, settings=self.settings)
        ]

        sorted_walked_paths = sorted(
            walked_paths
        )

        assert walked_paths == sorted_walked_paths

    def test_walk_pagination_filter(self):
        walk_paths = [
            link.walk_path
            for link
            in walk(file_path_to_file_uri(self.test_catalog.catalog_href), session=self.session, settings=self.settings)
        ]

        ref_walk_path_i = math.floor(len(walk_paths) / 2)
        ref_walk_path = walk_paths[ref_walk_path_i]

        walk_pagination_filter = make_walk_pagination_filter(
            start=ref_walk_path
        )

        filtered_walk = walk(file_path_to_file_uri(
            self.test_catalog.catalog_href), session=self.session, settings=self.settings)
        filtered_walk = walk_pagination_filter(filtered_walk)

        assert list(map(
            lambda walk_result: walk_result.walk_path,
            filtered_walk
        )) == walk_paths[ref_walk_path_i:]

        walk_pagination_filter = make_walk_pagination_filter(
            end=ref_walk_path
        )

        filtered_walk = walk(file_path_to_file_uri(
            self.test_catalog.catalog_href), session=self.session, settings=self.settings)
        filtered_walk = walk_pagination_filter(filtered_walk)

        assert list(map(
            lambda walk_result: walk_result.walk_path,
            filtered_walk
        )) == walk_paths[:(ref_walk_path_i + 1)]

    def test_walk_collections(self):
        collections = self.test_catalog.collections

        filtered_walk = walk_collections(
            file_path_to_file_uri(self.test_catalog.catalog_href),
            session=self.session,
            settings=self.settings
        )

        assert set(
            walk_result.resolve_id()
            for walk_result
            in filtered_walk
        ) == set(
            collection.id
            for collection
            in collections
        )

        collections = self.test_catalog.pick_collections(5)

        filtered_walk = walk_collections(
            file_path_to_file_uri(self.test_catalog.catalog_href),
            [
                collection.id
                for collection
                in collections

            ],
            session=self.session,
            settings=self.settings
        )

        assert set(
            walk_result.resolve_id()
            for walk_result
            in filtered_walk
        ) == set(
            collection.id
            for collection
            in collections
        )

    def test_walk_items(self):
        items = self.test_catalog.items

        filtered_walk = walk_items(
            file_path_to_file_uri(self.test_catalog.catalog_href),
            session=self.session,
            settings=self.settings
        )

        assert set(
            walk_result.resolve_id()
            for walk_result
            in filtered_walk
        ) == set(
            item.id
            for item
            in items
        )

        items = self.test_catalog.pick_items(5)

        filtered_walk = walk_items(
            file_path_to_file_uri(self.test_catalog.catalog_href),
            [
                item.id
                for item
                in items

            ],
            session=self.session,
            settings=self.settings
        )

        assert set(
            walk_result.resolve_id()
            for walk_result
            in filtered_walk
        ) == set(
            item.id
            for item
            in items
        )

    def test_walk_temporal_filters(self):
        datetimes = self.test_catalog.pick_datetime_intervals()

        for datetime in datetimes:
            match_datetime = make_match_datetime(datetime)
            match_temporal_extent = make_match_temporal_extent(datetime)

            matching_datetime = set(
                item.id
                for item
                in self.test_catalog.items
                if match_datetime(self._cast_item(item))
            )

            matching_temporal_extent = set(
                collection.id
                for collection
                in self.test_catalog.collections
                if match_temporal_extent(self._cast_collection(collection))
            )

            walk_datetime_filter = make_walk_datetime_filter(
                datetime=datetime
            )

            walk_temporal_extent_filter = make_walk_temporal_extent_filter(
                datetime=datetime,
            )

            matched_items = set(
                walk_result.resolve_id()
                for walk_result
                in walk_datetime_filter(
                    walk(
                        file_path_to_file_uri(self.test_catalog.catalog_href),
                        session=self.session,
                        settings=self.settings
                    )
                )
                if walk_result.type == Item
            )

            matched_collections = set(
                walk_result.resolve_id()
                for walk_result
                in walk_temporal_extent_filter(
                    walk_collections(
                        file_path_to_file_uri(self.test_catalog.catalog_href),
                        session=self.session,
                        settings=self.settings
                    )
                )
                if walk_result.type == Collection
            )

            assert matched_items == matching_datetime
            assert matched_collections == matching_temporal_extent

    def test_cql2_filter(self):
        items = self.test_catalog.pick_items()

        for item in items:
            item.properties["test"] = "test"

            match_cql2 = make_match_item_cql2("test = 'test'")

            assert match_cql2(Item.model_validate(item.to_dict()))
