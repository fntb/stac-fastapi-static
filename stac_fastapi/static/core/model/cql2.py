from typing import (
    Callable,
    Any,
    Union,
    Dict
)

import cql2
import datetime
import json

from stac_pydantic.item import Item
from stac_pydantic.collection import Collection

from ..errors import (
    BadStacObjectFilterError
)


def _sanitize_date_property(value: Any) -> Any:
    # The cql2 lirbary does not support dates
    if isinstance(value, (datetime.datetime, datetime.date)):
        return None
    else:
        return value


def make_match_item_cql2(
    filter: str | Dict
) -> Callable[[Item], bool]:

    if filter is not None:
        try:
            expr = cql2.Expr(filter)
            expr.validate()
        except (ValueError, TypeError, cql2.ValidationError) as error:
            raise BadStacObjectFilterError(
                f"Bad CQL2 Expression : Cannot parse cql2 expression : {json.dumps(filter)}"
            ) from error

        def match(item: Item) -> bool:
            properties_raw = item.properties.model_dump()
            properties = {
                property: _sanitize_date_property(properties_raw[property]) for property in properties_raw.keys() - {
                    "id",
                    "geometry",
                    "bbox",
                    "start_datetime",
                    "end_datetime",
                    "datetime"
                }
            }

            return expr.matches({
                "properties": properties

            })
    else:
        def match(item: Item) -> True:
            return True

    return match


def make_match_collection_cql2(
    filter: str | Dict
) -> Callable[[Collection], bool]:

    if filter is not None:
        try:
            expr = cql2.Expr(filter)
            expr.validate()
        except (ValueError, TypeError, cql2.ValidationError) as error:
            raise BadStacObjectFilterError(
                f"Bad CQL2 Expression : Cannot parse cql2 expression : {json.dumps(filter)}"
            ) from error

        def match(collection: Collection) -> bool:
            properties_raw = collection.model_dump()
            properties = {
                property: _sanitize_date_property(properties_raw[property]) for property in properties_raw.keys() - {
                    "type",
                    "id",
                    "stac_version",
                    "links",
                    "extent"
                }
            }

            try:
                return expr.matches({
                    "properties": properties

                })
            except Exception:
                return False
    else:
        def match(collection: Collection) -> True:
            return True

    return match
