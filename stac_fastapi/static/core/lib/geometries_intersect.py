
import shapely


def geometries_intersect(a: shapely.Geometry, b: shapely.Geometry) -> bool:
    return shapely.intersects(a, b)
