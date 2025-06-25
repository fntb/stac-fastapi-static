from typing import (
    Tuple
)

import shapely


def bbox_intersect(a: Tuple[float, float, float, float], b: Tuple[float, float, float, float]):
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def geometries_intersect(a: shapely.Geometry, b: shapely.Geometry) -> bool:
    return shapely.intersects(a, b)
