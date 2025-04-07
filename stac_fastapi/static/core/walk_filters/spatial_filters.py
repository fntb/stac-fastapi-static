
from typing import (
    Iterator,
    Callable,
    Optional
)

import logging

from stac_pydantic.shared import BBox
from geojson_pydantic.geometries import Geometry

from stac_pydantic.item import Item
from stac_pydantic.collection import Collection
from stac_pydantic.catalog import Catalog

from ..walk import (
    WalkResult,
    SkipWalk,
)

from ..errors import (
    BadStacObjectError
)

from .walk_filter import make_walk_filter, make_walk_filter_factory


from ..model import (
    make_match_geometry,
    make_match_bbox,
    make_match_spatial_extent
)

logger = logging.getLogger(__name__)


def make_spatial_extent_filter(
    geometry: Optional[Geometry | BBox] = None,
    assume_extent_spec: bool = True
) -> Callable[[WalkResult], bool]:

    match_spatial_extent = make_match_spatial_extent(
        geometry=geometry,
        assume_extent_spec=assume_extent_spec
    )

    def filter(walk_result: WalkResult) -> bool:
        if walk_result.type is Collection:
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

    return filter


def make_bbox_filter(
    bbox: Optional[BBox] = None,
    assume_extent_spec: bool = True
) -> Callable[[WalkResult], bool]:

    match_spatial_extent = make_match_spatial_extent(
        geometry=bbox,
        assume_extent_spec=assume_extent_spec
    )

    match_bbox = make_match_bbox(
        bbox=bbox
    )

    def filter(walk_result: WalkResult) -> bool:
        if not walk_result.is_resolved():
            walk_result.resolve()

        if walk_result.type is Item:
            try:
                return match_bbox(walk_result.object)
            except BadStacObjectError as error:
                logger.warning(f"Skipping walk_result : {str(walk_result)} : {str(error)}", extra={
                    "error": error
                })

                return False

        elif walk_result.type is Collection:
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

    return filter


def make_geometry_filter(
    geometry: Optional[Geometry] = None,
    assume_extent_spec: bool = True
) -> Callable[[WalkResult], bool]:

    match_spatial_extent = make_match_spatial_extent(
        geometry=geometry,
        assume_extent_spec=assume_extent_spec
    )

    match_geometry = make_match_geometry(
        geometry=geometry
    )

    def filter(walk_result: WalkResult) -> bool:
        if not walk_result.is_resolved():
            walk_result.resolve()

        if walk_result.type is Item:
            try:
                return match_geometry(walk_result.object)
            except BadStacObjectError as error:
                logger.warning(f"Skipping walk_result : {str(walk_result)} : {str(error)}", extra={
                    "error": error
                })

                return False

        elif walk_result.type is Collection:
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

    return filter


make_walk_spatial_extent_filter = make_walk_filter_factory(make_spatial_extent_filter)
make_walk_bbox_filter = make_walk_filter_factory(make_bbox_filter)
make_walk_geometry_filter = make_walk_filter_factory(make_geometry_filter)
