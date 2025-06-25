
from typing import (
    Optional,
    Callable,
    Tuple
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

from ..lib.geometries_intersect import (
    geometries_intersect,
    bbox_intersect
)


def get_bbox(geojson_feature: Feature) -> Tuple[float, float, float, float]:
    try:
        if geojson_feature.bbox is not None:
            return geojson_feature.bbox
        elif geojson_feature.geometry is not None:
            return shapely.geometry.shape(geojson_feature.geometry).bounds
        else:
            raise ValueError("Missing both bbox and geometry")
    except Exception as error:
        raise BadStacObjectError(
            "Bad STAC Object - Bad bbox : " + str(error),
            object=geojson_feature
        ) from error


def get_geometry(geojson_feature: Feature) -> shapely.Geometry | None:
    try:
        if geojson_feature.geometry is not None:
            return shapely.geometry.shape(geojson_feature.geometry)
        elif geojson_feature.bbox is not None:
            return None
        else:
            raise ValueError("Missing both bbox and geometry")
    except Exception as error:
        raise BadStacObjectError(
            "Bad STAC Object - Bad geometry : " + str(error),
            object=geojson_feature
        ) from error


def get_collection_bbox(collection: Collection) -> Tuple[float, float, float, float]:
    bboxes = collection.extent.spatial.bbox

    if not bboxes:
        raise BadStacObjectError("Bad STAC Collection - Missing spatial extent", object=collection)
    else:
        return bboxes[0]


def get_collection_geometry(collection: Collection) -> shapely.Polygon | None:
    bboxes = collection.extent.spatial.bbox

    if not bboxes:
        raise BadStacObjectError("Bad STAC Collection - Missing spatial extent", object=collection)
    elif len(bboxes) == 1:
        return None
    else:
        return shapely.union_all([
            shapely.box(*bbox)
            for bbox
            in bboxes[1:]
        ])


def make_match_spatial_extent(
    bbox: Optional[BBox] = None,
    geometry: Optional[Geometry] = None
) -> Callable[[Collection], bool]:
    if geometry is None and bbox is None:
        def match(collection: Collection) -> bool:
            return True
    else:

        if geometry is not None:
            try:
                geometry = shapely.geometry.shape(geometry)
            except Exception as error:
                raise BadStacObjectFilterError(
                    f"Bad geometry : {str(error)}"
                ) from error
        else:
            geometry = shapely.box(*bbox)

        if bbox is None:
            bbox = shapely.bounds(geometry)

        def match(collection: Collection) -> bool:
            collection_bbox = get_collection_bbox(collection)

            if not bbox_intersect(collection_bbox, bbox):
                return False

            collection_geometry = get_collection_geometry(collection)

            if collection_geometry is None:
                return True

            return geometries_intersect(collection_geometry, geometry)

    return match


def make_match_bbox(
    bbox: Optional[BBox] = None
) -> Callable[[Item], bool]:

    if bbox is None:
        def match(item: Item) -> bool:
            return True
    else:
        def match(item: Item):
            item_bbox = get_bbox(item)

            return bbox_intersect(bbox, item_bbox)

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
            bbox = shapely.bounds(geometry)
        except Exception as error:
            raise BadStacObjectFilterError(
                f"Bad geometry : {str(error)}"
            ) from error

        def match(item: Item):
            item_bbox = get_bbox(item)

            if not bbox_intersect(bbox, item_bbox):
                return False

            item_geometry = get_geometry(item)

            return geometries_intersect(geometry, item_geometry)

    return match
