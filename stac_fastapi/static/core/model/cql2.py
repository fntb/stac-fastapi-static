from typing import (
    Callable,
    Any,
    Union,
    Dict
)

import pygeofilter
import pygeofilter.backends
import pygeofilter.backends.cql2_json
import pygeofilter.parsers
import pygeofilter.parsers.cql2_text
import pygeofilter.parsers.cql2_json

from pygeofilter.ast import AstType as CQL2Ast

from pygeofilter.backends.native.evaluate import NativeEvaluator

import json

from stac_pydantic.item import Item
from stac_pydantic.collection import Collection

from ..errors import (
    BadStacObjectFilterError
)


def make_match_item_cql2(
    cql2: Union[CQL2Ast, Dict]
) -> Callable[[Item], bool]:

    if cql2 is not None:
        try:
            cql2_filter_ast = pygeofilter.parsers.cql2_json.parse(cql2)
        except ValueError as error:
            raise BadStacObjectFilterError(
                f"Bad CQL2 Expression : Cannot parse cql2 expression : {json.dumps(cql2)}"
            ) from error

        cql2: Callable[[Any], bool] = NativeEvaluator(
            attribute_map={
                "id": "id",
                "geometry": "geometry",
                "bbox": "bbox",
                "*": "properties.*"
            },
            use_getattr=False
        ).evaluate(cql2_filter_ast)

        def match(item: Item) -> bool:
            try:
                return cql2(item.model_dump())
            except Exception:
                return False
    else:
        def match(item: Item) -> True:
            return True

    return match


def make_match_collection_cql2(
    cql2: Union[CQL2Ast, Dict]
) -> Callable[[Collection], bool]:

    if cql2 is not None:
        try:
            cql2_filter_ast = pygeofilter.parsers.cql2_json.parse(cql2)
        except ValueError as error:
            raise BadStacObjectFilterError(
                f"Bad CQL2 Expression : Cannot parse cql2 expression : {str(error)}"
            ) from error

        cql2: Callable[[Any], bool] = NativeEvaluator(
            attribute_map={
                "id": "id",
                "bbox": "extent.spatial.bbox.0",
                "*": "*"
            },
            use_getattr=False
        ).evaluate(cql2_filter_ast)

        def match(collection: Collection) -> bool:
            return cql2(collection.model_dump())
    else:
        def match(collection: Collection) -> True:
            return True

    return match
