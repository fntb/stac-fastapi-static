from typing import (
    Optional,
    Any
)
import random
import datetime as datetimelib
import json

import shapely
import pystac

from .generate_id import generate_id
from .generate_text import generate_title_and_description_props
from .generate_datetime import generate_start_end_datetime, generate_datetime
from .generate_geometry import generate_geometry


def generate_item(
        datetime: Optional[datetimelib.datetime | tuple[datetimelib.datetime, datetimelib.datetime]] = None,
        geometry: Optional[shapely.Polygon | Any] = None,
        geometry_restriction: Optional[shapely.Polygon] = None,
        datetime_restriction: Optional[tuple[datetimelib.datetime, datetimelib.datetime]] = None,
):
    if geometry is None:
        (geometry, bbox) = generate_geometry(geometry_restriction)
    else:
        if isinstance(geometry, shapely.Geometry):
            geometry = json.loads(shapely.to_geojson(geometry))

        bbox = shapely.from_geojson(json.dumps(geometry)).bounds

    if datetime is None:
        if random.randint(0, 1):
            datetime = generate_datetime(datetime_restriction)
        else:
            datetime = generate_start_end_datetime(datetime_restriction)

    item = pystac.Item(
        generate_id(),
        geometry=geometry,
        bbox=bbox,
        datetime=datetime if isinstance(
            datetime, datetimelib.datetime) else None,
        properties={
            **generate_title_and_description_props(),
        },
        start_datetime=datetime[0] if isinstance(datetime, tuple) else None,
        end_datetime=datetime[1] if isinstance(datetime, tuple) else None
    )

    return item
