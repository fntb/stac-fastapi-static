
from typing import (
    Optional,
)

import logging
import time

from stac_pydantic.shared import BBox
from geojson_pydantic.geometries import Geometry

from stac_pydantic.item import Item
from stac_pydantic.collection import Collection
from stac_pydantic.catalog import Catalog

from .errors import (
    BadStacObjectError
)

from .walk import (
    WalkResult,
    SkipWalk,
)


from .model import (
    make_match_geometry,
    make_match_bbox,
    make_match_spatial_extent
)

logger = logging.getLogger(__name__)


def make_filter_collections_spatial_extent(
    *,
    bbox: Optional[BBox] = None,
    geometry: Optional[Geometry] = None,
):
    match_spatial_extent = make_match_spatial_extent(
        bbox=bbox,
        geometry=geometry,
    )

    def filter_collections_spatial_extent(walk_result: WalkResult) -> bool:
        if walk_result.type == (Collection, Catalog):
            walk_result.resolve()

        if walk_result.type == Collection:
            try:
                matches_spatial_extent = match_spatial_extent(walk_result.object)
            except BadStacObjectError as error:
                logger.warning(f"Skipping walk_result (not branch) : {str(walk_result)} : {str(error)}", extra={
                    "error": error
                })

                return False

            if matches_spatial_extent:
                return True
            else:
                raise SkipWalk
        else:
            return True

    return filter_collections_spatial_extent


def make_filter_items_spatial_extent(
    *,
    bbox: Optional[BBox] = None,
    geometry: Optional[Geometry] = None,
):
    match_bbox = make_match_bbox(bbox)
    match_geometry = make_match_geometry(geometry)
    match_spatial_extent = make_match_spatial_extent(
        bbox=bbox,
        geometry=geometry,
    )

    def filter_items_spatial_extent(walk_result: WalkResult) -> bool:
        if not walk_result.is_resolved():
            walk_result.resolve()

        if walk_result.type == Item:
            try:
                return match_bbox(walk_result.object) and match_geometry(walk_result.object)
            except BadStacObjectError as error:
                logger.warning(f"Skipping walk_result : {str(walk_result)} : {str(error)}", extra={
                    "error": error
                })

                return False

        elif walk_result.type == Collection:
            try:
                matches_spatial_extent = match_spatial_extent(walk_result.object)
            except BadStacObjectError as error:
                logger.info(f"Skipping walk_result (not branch) : {str(walk_result)} : {str(error)}", extra={
                    "error": error
                })

                return False

            if matches_spatial_extent:
                return True
            else:
                raise SkipWalk
        else:
            return True

    return filter_items_spatial_extent
