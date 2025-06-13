from typing import (
    NamedTuple,
    Optional,
    Any
)

import random
import json

import shapely


class GeometryAndBBox(NamedTuple):
    geometry: Any
    bbox: tuple[float, float, float, float]


def generate_geometry(
    restriction: Optional[shapely.Polygon] | tuple[float,
                                                   float, float, float] | None = (-180, -90, 180, 90),
    size: Optional[tuple[float, float]] = (0.1, 0.1)
) -> GeometryAndBBox:
    dx = size[0]
    dy = size[1] / 2

    if restriction is None:
        restriction_bbox = (-180, -90, 180, 90)
    elif isinstance(restriction, (tuple, list)):
        restriction_bbox = restriction
    else:
        restriction_bbox = restriction.bounds

    Dx = restriction_bbox[2] - restriction_bbox[0]
    Dy = restriction_bbox[3] - restriction_bbox[1]

    x = random.random() * (Dx - 2*dx) - (Dx / 2 - dx)
    y = random.random() * (Dy - 2*dy) - (Dy / 2 - dy)

    bbox = (
        x, y, max(x + dx, restriction_bbox[2]), max(y + dy, restriction_bbox[3]))
    geometry = shapely.box(*bbox)

    return GeometryAndBBox(
        geometry=json.loads(shapely.to_geojson(geometry)),
        bbox=bbox
    )
