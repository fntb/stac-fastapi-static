
from typing import (
    Iterator,
    Callable,
    Optional
)

import datetime as datetimelib
import logging

from stac_pydantic.item import Item
from stac_pydantic.collection import Collection
from stac_pydantic.catalog import Catalog

from ..errors import (
    BadStacObjectError
)

from ..walk import (
    WalkResult,
    SkipWalk,
)

from .walk_filter import (
    make_walk_filter,
    make_walk_filter_factory
)

from ..model import (
    make_match_datetime,
    make_match_temporal_extent,
)

logger = logging.getLogger(__name__)


def make_temporal_extent_filter(
    datetime: Optional[datetimelib.datetime | tuple[datetimelib.datetime | None, datetimelib.datetime | None]] = None,
    assume_extent_spec: bool = True
) -> Callable[[WalkResult], bool]:

    match_temporal_extent = make_match_temporal_extent(
        datetime=datetime,
        assume_extent_spec=assume_extent_spec
    )

    def filter(walk_result: WalkResult) -> bool:

        if walk_result.type is Catalog:
            walk_result.resolve()

        if walk_result.type is Collection:
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

    return filter


def make_datetime_filter(
    datetime: Optional[datetimelib.datetime | tuple[datetimelib.datetime | None, datetimelib.datetime | None]] = None,
    assume_extent_spec: bool = True
) -> Callable[[WalkResult], bool]:

    match_datetime = make_match_datetime(
        datetime=datetime
    )

    match_temporal_extent = make_match_temporal_extent(
        datetime=datetime,
        assume_extent_spec=assume_extent_spec
    )

    def filter(walk_result: WalkResult) -> bool:
        walk_result.resolve()

        if walk_result.type is Collection:
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
        elif walk_result.type is Item:
            try:
                return match_datetime(walk_result.object)
            except BadStacObjectError as error:
                logger.warning(f"Skipping walk_result : {str(walk_result)} : {str(error)}", extra={
                    "error": error
                })

                return False
        else:
            return True

    return filter


make_walk_temporal_extent_filter = make_walk_filter_factory(make_temporal_extent_filter)

make_walk_datetime_filter = make_walk_filter_factory(make_datetime_filter)
