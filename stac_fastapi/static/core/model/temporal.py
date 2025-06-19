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

from ..lib.datetimes_intersect import datetimes_intersect


def get_datetime(stac_object: Item | Collection | Catalog) -> datetimelib.datetime | tuple[datetimelib.datetime, datetimelib.datetime]:

    if isinstance(stac_object, Item):
        common_metadata = stac_object.properties
    else:
        # no validation required, common metadata should be present ?
        common_metadata: StacCommonMetadata = stac_object

    if common_metadata.start_datetime and common_metadata.end_datetime:
        return (fromisoformat(common_metadata.start_datetime), fromisoformat(common_metadata.end_datetime))
    elif common_metadata.datetime:
        return fromisoformat(common_metadata.datetime)
    else:
        raise BadStacObjectError(
            "Bad STAC Object - Common metadata are missing both datetime and start_datetime/end_datetime",
            object=stac_object
        )


def get_temporal_extent(collection: Collection) -> list[tuple[datetimelib.datetime | None, datetimelib.datetime | None]]:
    intervals = collection.extent.temporal.interval

    def parse_interval(*datetimes_str: str):
        try:
            return (
                fromisoformat(datetimes_str[0]) if datetimes_str[0] is not None else None,
                fromisoformat(datetimes_str[1]) if datetimes_str[1] is not None else None
            )
        except Exception as error:
            raise BadStacObjectError(
                "Bad STAC Collection - Bad temporal extent : Bad datetime interval : " + str(error),
                object=collection
            ) from error

    try:
        (overall_interval, intervals) = (intervals[0], intervals[1:])
    except KeyError as error:
        raise BadStacObjectError(
            "Bad STAC Collection - Missing temporal extent",
            object=collection
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


def make_match_temporal_extent(
    datetime: Optional[datetimelib.datetime | tuple[datetimelib.datetime | None, datetimelib.datetime | None]] = None,
) -> Callable[[Collection], bool]:

    if datetime is None:
        def match(collection: Collection) -> True:
            return True
    else:
        def match(collection: Collection) -> bool:
            collection_extent = get_temporal_extent(
                collection,
            )

            for interval in collection_extent:
                if datetimes_intersect(datetime, interval):
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
            return datetimes_intersect(datetime, item_datetime)

    return match
