from typing import (
    Dict,
    Optional
)

import logging

from stac_pydantic.item import Item
from stac_pydantic.collection import Collection
from stac_pydantic.catalog import Catalog

from .walk import (
    WalkResult,
)


from .model import (
    make_match_collection_cql2,
    make_match_item_cql2,
)


logger = logging.getLogger(__name__)


def make_filter_items_cql2(cql2: Optional[str | Dict] = None):

    match_cql2 = make_match_item_cql2(cql2)

    def filter_items_cql2(walk_result: WalkResult) -> bool:
        if walk_result.type == Item:
            try:
                return match_cql2(walk_result.resolve())
            except Exception as error:
                logger.warning(f"Skipping walk_result (not branch) : {str(walk_result)} : {str(error)}", extra={
                    "error": error
                })

                return False
        else:
            return True

    return filter_items_cql2


def make_filter_collections_cql2(cql2: Optional[str | Dict] = None):

    match_cql2 = make_match_collection_cql2(cql2)

    def filter_collections_cql2(walk_result: WalkResult) -> bool:
        if walk_result.type == (Collection, Catalog):
            walk_result.resolve()

        if walk_result.type == Collection:
            try:
                return match_cql2(walk_result.resolve())
            except Exception as error:
                logger.warning(f"Skipping walk_result : {str(walk_result)} : {str(error)}", extra={
                    "error": error
                })

                return False
        else:
            return True

    return filter_collections_cql2
