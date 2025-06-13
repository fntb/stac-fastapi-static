from typing import (
    Callable,
    Generator,
    Optional,
    Any
)

import datetime as datetimelib
import pystac
import pystac.summaries
import shapely

from .generate_id import generate_id
from .generate_text import generate_title_and_description_props
from .generate_item import generate_item
from .generate_geometry import generate_geometry
from .generate_datetime import generate_start_end_datetime


def generate_collection(
    shape: tuple[int, int] | Callable[[int], tuple[int, int]] = (0, 1),
    datetime: Optional[datetimelib.datetime | tuple[datetimelib.datetime, datetimelib.datetime]] = None,
    geometry: Optional[shapely.Polygon | Any] = None,
    geometry_restriction: Optional[shapely.Polygon] = None,
    datetime_restriction: Optional[tuple[datetimelib.datetime, datetimelib.datetime]] = None,
    _current_depth: int = 1,
) -> Generator[pystac.Item | pystac.Collection, None, pystac.Collection]:

    (item_count, child_count) = shape if isinstance(
        shape, (tuple, list)) else shape(_current_depth)

    if isinstance(datetime, datetimelib.datetime):
        datetime = (datetime, datetime)

    if geometry is not None and not isinstance(geometry, shapely.Geometry):
        geometry = shapely.geometry.shape(geometry)

    geometry_restriction = generate_geometry(
        restriction=geometry_restriction or geometry,
        size=(10 / _current_depth, 10 / _current_depth)
    ).bbox

    datetime_restriction = generate_start_end_datetime(
        restriction=datetime_restriction or datetime,
        duration=datetimelib.timedelta(days=30 / _current_depth)
    )

    items = [
        generate_item(
            geometry_restriction=geometry_restriction,
            datetime_restriction=datetime_restriction
        ) for _ in range(item_count)
    ]

    title_and_description = generate_title_and_description_props()

    extent = pystac.Extent.from_items(items)

    if geometry:
        extent.spatial.bboxes[0] = geometry.bounds

    if datetime:
        extent.temporal.intervals[0] = datetime

    collection = pystac.Collection(
        generate_id(),
        title_and_description["description"],
        extent,
        extra_fields={
            **title_and_description
        },
        summaries=pystac.summaries.Summarizer().summarize(items)
    )

    yield collection

    for item in items:
        collection.add_item(item)
        yield item

    for _ in range(child_count):
        sub_collection = yield from generate_collection(
            shape,
            geometry_restriction=geometry_restriction,
            datetime_restriction=datetime_restriction,
            _current_depth=_current_depth + 1
        )

        yield sub_collection

        collection.add_child(sub_collection)
        collection.summaries.combine(sub_collection.summaries)

        # generated = generate_collection(
        #     shape,
        #     _current_depth=_current_depth + 1
        # )

        # sub_collection = next(generated)

        # yield sub_collection

        # collection.add_child(sub_collection)
        # collection.summaries.combine(sub_collection.summaries)

        # yield from generated

    return collection
