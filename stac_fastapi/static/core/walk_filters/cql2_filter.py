from typing import (
    Optional,
    Callable,
    Iterator,
    Any,
    Union,
    Dict
)

import cql2
import orjson
import logging

from stac_pydantic.item import Item
from stac_pydantic.collection import Collection
from stac_pydantic.catalog import Catalog

from ..walk import (
    WalkResult,
)

from ..errors import (
    BadStacObjectFilterError
)

from .walk_filter import make_walk_filter, make_walk_filter_factory

from ..model import (
    make_match_collection_cql2,
    make_match_item_cql2,
)

logger = logging.getLogger(__name__)

# def parse_cql2_str(
#     cql2_expr: str | dict[str, Any],
#     cql2_lang: Optional[str] = "cql2-text",
# ) -> dict[str, Any]:
#     try:
#         if cql2_lang == "cql2-json":
#             if isinstance(cql2_expr, str):
#                 expr = cql2.Expr(orjson.loads(cql2_expr))
#             else:
#                 expr = cql2.Expr(cql2_expr)
#         elif cql2_lang == "cql2-text":
#             expr = cql2.Expr(cql2_expr)
#         else:
#             raise BadStacObjectFilterError("Bad CQL2 Expression Language - Expected one of 'cql2-json' or 'cql2-text'")

#         expr.validate()
#     except cql2.ValidationError as error:
#         raise BadStacObjectFilterError("Bad CQL2 Expression") from error

#     return expr.to_json()


def make_item_cql2_filter(
    cql2: str | Dict
) -> Callable[[WalkResult], bool]:

    match_cql2 = make_match_item_cql2(cql2)

    def filter(walk_result: WalkResult) -> bool:
        if walk_result.type is Item:
            try:
                return match_cql2(walk_result.resolve())
            except Exception as error:
                logger.warning(f"Skipping walk_result (not branch) : {str(walk_result)} : {str(error)}", extra={
                    "error": error
                })

                return False
        else:
            return True

    return filter


def make_collection_cql2_filter(
    cql2: str | Dict
) -> Callable[[WalkResult], bool]:

    match_cql2 = make_match_collection_cql2(cql2)

    def filter(walk_result: WalkResult) -> bool:
        if walk_result.type in (Collection, Catalog):
            walk_result.resolve()

        if walk_result.type is Collection:
            try:
                return match_cql2(walk_result.resolve())
            except Exception as error:
                logger.warning(f"Skipping walk_result : {str(walk_result)} : {str(error)}", extra={
                    "error": error
                })

                return False
        else:
            return True

    return filter


make_walk_item_cql2_filter = make_walk_filter_factory(make_item_cql2_filter)
make_walk_collection_cql2_filter = make_walk_filter_factory(make_collection_cql2_filter)
