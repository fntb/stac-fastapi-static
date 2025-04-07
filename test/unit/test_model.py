from typing import (
    Optional
)

import datetime as datetimelib

import pytest

import pystac
import shapely

from stac_pydantic.item import Item
from stac_pydantic.collection import Collection
from stac_pydantic.shared import BBox
from geojson_pydantic.geometries import Geometry


from stac_test_tools import (
    generate_item,
    generate_collection
)

from stac_fastapi.static.core.walk_filters.temporal_filters import (
    make_match_datetime,
    make_match_temporal_extent,
)
from stac_fastapi.static.core.walk_filters.spatial_filters import (
    make_match_geometry,
    make_match_bbox,
    make_match_spatial_extent
)
from stac_fastapi.static.core.walk_filters.cql2_filter import (
    make_match_item_cql2
)


class TestModel():

    @staticmethod
    def _make_item(
        geometry: Optional[shapely.Geometry] = None,
        datetime: Optional[datetimelib.datetime | tuple[datetimelib.datetime, datetimelib.datetime]] = None,
    ):
        return Item.model_validate(generate_item(
            geometry=geometry,
            datetime=datetime
        ).to_dict(include_self_link=False))

    @staticmethod
    def _make_collection(
        geometry: Optional[shapely.Geometry] = None,
        datetime: Optional[datetimelib.datetime | tuple[datetimelib.datetime, datetimelib.datetime]] = None,
    ):
        return Collection.model_validate(next(generate_collection(
            geometry=geometry,
            datetime=datetime
        )).to_dict(include_self_link=False))

    @staticmethod
    def _datetime_to_str(datetime: datetimelib.datetime | tuple[datetimelib.datetime, datetimelib.datetime]) -> str:
        if isinstance(datetime, datetimelib.datetime):
            return datetime.isoformat()
        else:
            return f"{datetime[0].isoformat()}/{datetime[1].isoformat()}"

    def test_spatial_matches(self):
        match_bbox = make_match_bbox((0, 0, 3, 3))
        match_geometry = make_match_geometry(shapely.box(0, 0, 3, 3))
        match_spatial_extent = make_match_spatial_extent(shapely.box(0, 0, 3, 3))

        for bbox in [
            (1, 1, 2, 2),
            (2, 1, 4, 2),
            (-1, 2, 1, 4),
            (-1, -1, 4, 4)
        ]:
            assert match_bbox(self._make_item(geometry=shapely.box(*bbox)))
            assert match_geometry(self._make_item(geometry=shapely.box(*bbox)))
            assert match_spatial_extent(self._make_collection(geometry=shapely.box(*bbox)))

        for bbox in [
            (4, 0, 7, 3)
        ]:
            assert not match_bbox(self._make_item(geometry=shapely.box(*bbox)))
            assert not match_geometry(self._make_item(geometry=shapely.box(*bbox)))
            assert not match_spatial_extent(self._make_collection(geometry=shapely.box(*bbox)))

    def test_temporal_matches(self):

        seconds = [
            (time, time + 1)
            for time in range(5)
        ]

        query_second = ((seconds[1][0] + seconds[1][1]) / 2, (seconds[3][0] + seconds[3][1]) / 2)

        k = datetimelib.datetime.now().timestamp() / (seconds[-1][1] - seconds[0][0])

        datetimes = [
            (
                datetimelib.datetime.fromtimestamp(second[0] * k, tz=datetimelib.timezone.utc),
                datetimelib.datetime.fromtimestamp(second[1] * k, tz=datetimelib.timezone.utc)
            )
            for second in seconds
        ]

        query_datetime = (
            datetimelib.datetime.fromtimestamp(query_second[0] * k, tz=datetimelib.timezone.utc),
            datetimelib.datetime.fromtimestamp(query_second[1] * k, tz=datetimelib.timezone.utc)
        )

        match_datetime = make_match_datetime(query_datetime)
        match_temporal_extent = make_match_temporal_extent(query_datetime)

        def make_msg(a, b):
            return f"{self._datetime_to_str(a)} vs. {self._datetime_to_str(b)}"

        for datetime in [
            datetimes[1],
            datetimes[2],
            datetimes[3],
            datetimes[2][0],
            datetimes[3][0]
        ]:
            item = self._make_item(datetime=datetime)
            collection = self._make_collection(datetime=datetime)

            assert match_datetime(item), make_msg(query_datetime, datetime)
            assert match_temporal_extent(collection), make_msg(query_datetime, datetime)

        for datetime in [
            datetimes[0],
            datetimes[4],
            datetimes[0][0],
            datetimes[1][0],
            datetimes[4][0]
        ]:
            item = self._make_item(datetime=datetime)
            collection = self._make_collection(datetime=datetime)

            assert not match_datetime(item), make_msg(query_datetime, datetime)
            assert not match_temporal_extent(collection), make_msg(query_datetime, datetime)

        match_datetime = make_match_datetime(query_datetime[0])
        match_temporal_extent = make_match_temporal_extent(query_datetime[0])

        for datetime in [
            datetimes[1]
        ]:
            item = self._make_item(datetime=datetime)
            collection = self._make_collection(datetime=datetime)

            assert match_datetime(item), make_msg(query_datetime[0], datetime)
            assert match_temporal_extent(collection), make_msg(query_datetime[0], datetime)

        for datetime in [
            datetimes[0],
            datetimes[2],
            datetimes[3],
            datetimes[4],
            datetimes[0][0],
            datetimes[1][0],
            datetimes[2][0],
            datetimes[3][0],
            datetimes[4][0]
        ]:
            item = self._make_item(datetime=datetime)
            collection = self._make_collection(datetime=datetime)

            assert not match_datetime(item), make_msg(query_datetime[0], datetime)
            assert not match_temporal_extent(collection), make_msg(query_datetime[0], datetime)

    @pytest.mark.skip("Not Implemented Yet")
    def test_cql2_match(self):
        ...
