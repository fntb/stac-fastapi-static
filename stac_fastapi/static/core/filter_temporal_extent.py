
from typing import (
    Optional,
    Callable
)

import datetime as datetimelib
import logging

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
    make_match_datetime,
    make_match_temporal_extent,
)

logger = logging.getLogger(__name__)


def make_filter_collections_temporal_extent(
    datetime: Optional[datetimelib.datetime | tuple[datetimelib.datetime | None, datetimelib.datetime | None]] = None,
) -> Callable[[WalkResult], bool]:

    match_temporal_extent = make_match_temporal_extent(
        datetime=datetime,
    )

    def filter_collections_temporal_extent(walk_result: WalkResult) -> bool:
        if walk_result.type == (Collection, Catalog):
            walk_result.resolve()

        if walk_result.type == Collection:
            try:
                matches_temporal_extent = match_temporal_extent(walk_result.object)
            except BadStacObjectError as error:
                logger.warning(f"Skipping walk_result (not branch) : {str(walk_result)} : {str(error)}", extra={
                    "error": error
                })

                return False

            if matches_temporal_extent:
                return True
            else:
                raise SkipWalk
        else:
            return True

    return filter_collections_temporal_extent


def make_filter_items_temporal_extent(
    datetime: Optional[datetimelib.datetime | tuple[datetimelib.datetime | None, datetimelib.datetime | None]] = None,
):
    match_datetime = make_match_datetime(
        datetime=datetime
    )

    match_temporal_extent = make_match_temporal_extent(
        datetime=datetime,
    )

    def filter_items_temporal_extent(walk_result: WalkResult) -> bool:
        if not walk_result.is_resolved():
            walk_result.resolve()

        if walk_result.type == Collection:
            try:
                matches_temporal_extent = match_temporal_extent(walk_result.object)
            except BadStacObjectError as error:
                logger.info(f"Skipping walk_result (not branch) : {str(walk_result)} : {str(error)}", extra={
                    "error": error
                })

                return False

            if matches_temporal_extent:
                return True
            else:
                raise SkipWalk
        elif walk_result.type == Item:
            try:
                return match_datetime(walk_result.object)
            except BadStacObjectError as error:
                logger.warning(f"Skipping walk_result : {str(walk_result)} : {str(error)}", extra={
                    "error": error
                })

                return False
        else:
            return True

    return filter_items_temporal_extent
