
from typing import (
    Optional,
    Callable,
)

import shapely
import shapely.geometry

from geojson_pydantic import Feature
from geojson_pydantic.geometries import Geometry

from stac_pydantic.collection import Collection
from stac_pydantic.item import Item

from stac_pydantic.shared import BBox

from ..errors import (
    BadStacObjectError,
    BadStacObjectFilterError
)


def get_bbox(geojson_feature: Feature) -> shapely.Polygon:
    try:
        return shapely.box(*geojson_feature.bbox)
    except Exception as error:
        raise BadStacObjectError(
            "Bad STAC Object - Bad bbox : " + str(error)
        ) from error


def get_geometry(geojson_feature: Feature) -> shapely.Geometry:
    try:
        return shapely.geometry.shape(geojson_feature.geometry)
    except Exception as error:
        raise BadStacObjectError(
            "Bad STAC Object - Bad geometry : " + str(error)
        ) from error


def get_spatial_extent(collection: Collection, assume_extent_spec: bool = True) -> shapely.Polygon:
    bboxes = collection.extent.spatial.bbox

    try:
        if assume_extent_spec:
            return shapely.box(*bboxes[0])
        else:
            return shapely.union_all([
                shapely.box(*bbox)
                for bbox
                in bboxes
            ])
    except Exception as error:
        raise BadStacObjectError(
            "Bad STAC Collection - Bad spatial extent : " + str(error)
        ) from error


def make_match_spatial_extent(
    geometry: Optional[Geometry | BBox] = None,
    assume_extent_spec: bool = True
) -> Callable[[Collection], bool]:

    if geometry is None:
        def match(collection: Collection) -> bool:
            return True
    else:
        try:
            if isinstance(geometry, (tuple, list)):
                geometry: shapely.Polygon = shapely.box(*geometry)
            else:
                geometry = shapely.geometry.shape(geometry)
        except Exception as error:
            raise BadStacObjectFilterError(
                f"Bad geometry : {str(error)}"
            ) from error

        def match(collection: Collection) -> bool:
            collection_extent_geometry = get_spatial_extent(collection, assume_extent_spec=assume_extent_spec)

            return shapely.intersects(geometry, collection_extent_geometry)

    return match


def make_match_bbox(
    bbox: Optional[BBox] = None
) -> Callable[[Item], bool]:

    if bbox is None:
        def match(item: Item) -> bool:
            return True
    else:
        try:
            bbox: shapely.Polygon = shapely.box(*bbox)
        except Exception as error:
            raise BadStacObjectFilterError(
                f"Bad bbox : {str(error)}"
            ) from error

        def match(item: Item):
            item_bbox = get_bbox(item)

            return shapely.intersects(bbox, item_bbox)

    return match


def make_match_geometry(
    geometry: Optional[Geometry] = None,
) -> Callable[[Item], bool]:

    if geometry is None:
        def match(item: Item) -> True:
            return True
    else:
        try:
            geometry = shapely.geometry.shape(geometry)
        except Exception as error:
            raise BadStacObjectFilterError(
                f"Bad geometry : {str(error)}"
            ) from error

        def match(item: Item):
            item_geometry = get_geometry(item)

            return shapely.intersects(geometry, item_geometry)

    return match
