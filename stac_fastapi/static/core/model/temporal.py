from typing import (
    Optional,
    Callable
)

import datetime as datetimelib

from stac_pydantic.collection import Collection
from stac_pydantic.catalog import Catalog
from stac_pydantic.item import Item

from stac_pydantic.shared import StacCommonMetadata

from ..compat import fromisoformat

from ..errors import (
    BadStacObjectError
)


def get_datetime(stac_object: Item | Collection | Catalog) -> datetimelib.datetime | tuple[datetimelib.datetime, datetimelib.datetime]:

    if isinstance(stac_object, Item):
        common_metadata = stac_object.properties
    else:
        # no validation required, common metadata should be present ?
        common_metadata: StacCommonMetadata = stac_object

    if common_metadata.datetime:
        return common_metadata.datetime
    elif common_metadata.start_datetime and common_metadata.end_datetime:
        return (common_metadata.start_datetime, common_metadata.end_datetime)
    else:
        raise BadStacObjectError(
            "Bad STAC Object - Common metadata are missing both datetime and start_datetime/end_datetime"
        )


def get_temporal_extent(collection: Collection, assume_extent_spec: bool = True) -> list[tuple[datetimelib.datetime | None, datetimelib.datetime | None]]:
    intervals = collection.extent.temporal.interval

    def parse_interval(*datetimes_str: str):
        try:
            return (
                fromisoformat(datetimes_str[0]) if datetimes_str[0] is not None else None,
                fromisoformat(datetimes_str[1]) if datetimes_str[1] is not None else None
            )
        except Exception as error:
            raise BadStacObjectError(
                "Bad STAC Collection - Bad temporal extent : Bad datetime interval : " + str(error)
            ) from error

    if assume_extent_spec:
        try:
            (overall_interval, intervals) = (intervals[0], intervals[1:])
        except KeyError as error:
            raise BadStacObjectError(
                "Bad STAC Collection - Bad temporal extent : Empty extent " + str(error)
            ) from error

        if intervals:
            return [
                parse_interval(*interval)
                for interval
                in intervals
            ]
        else:
            return [
                parse_interval(*overall_interval)
            ]
    else:
        return [
            parse_interval(*interval)
            for interval
            in intervals
        ]


def _intersect_datetime_and_interval(
        datetime: datetimelib.datetime,
        interval: tuple[datetimelib.datetime | None, datetimelib.datetime | None]
) -> bool:
    return (interval[0] is None or datetime >= interval[0]) and (interval[1] is None or datetime <= interval[1])


def _intersect_intervals(
    interval_a: tuple[datetimelib.datetime | None, datetimelib.datetime | None],
    interval_b: tuple[datetimelib.datetime | None, datetimelib.datetime | None]
) -> bool:
    return (
        interval_a[0] is None or interval_b[1] is None or interval_a[0] <= interval_b[1]
    ) and (
        interval_a[1] is None or interval_b[0] is None or interval_a[1] >= interval_b[0]
    )


def _intersect(
        a: tuple[datetimelib.datetime | None, datetimelib.datetime | None] | datetimelib.datetime,
        b: tuple[datetimelib.datetime | None, datetimelib.datetime | None] | datetimelib.datetime
):
    if isinstance(a, datetimelib.datetime) and isinstance(b, datetimelib.datetime):
        return a == b
    elif isinstance(a, datetimelib.datetime):
        return _intersect_datetime_and_interval(a, b)
    elif isinstance(b, datetimelib.datetime):
        return _intersect_datetime_and_interval(b, a)
    else:
        return _intersect_intervals(a, b)


def make_match_temporal_extent(
    datetime: Optional[datetimelib.datetime | tuple[datetimelib.datetime | None, datetimelib.datetime | None]] = None,
    assume_extent_spec: bool = True
) -> Callable[[Collection], bool]:

    if datetime is None:
        def match(collection: Collection) -> True:
            return True
    else:
        def match(collection: Collection) -> bool:
            collection_extent = get_temporal_extent(
                collection,
                assume_extent_spec=assume_extent_spec
            )

            for interval in collection_extent:
                if _intersect(datetime, interval):
                    return True

            return False

    return match


def make_match_datetime(
    datetime: Optional[datetimelib.datetime | tuple[datetimelib.datetime | None, datetimelib.datetime | None]] = None
) -> Callable[[Item], bool]:

    if datetime is None:
        def match(item: Item) -> True:
            return True
    else:
        def match(item: Item) -> bool:
            item_datetime = get_datetime(item)
            return _intersect(datetime, item_datetime)

    return match
