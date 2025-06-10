from typing import (
    Optional,
    List,
    Optional,
    Union,
    Tuple,
    Dict,
    Annotated,
    ClassVar,
    Literal,
    Type,
    TypeVar,
    Generic,
    Any,
    Dict
)

import datetime as datetimelib
import json
import orjson

from functools import cached_property

from pydantic import (
    BaseModel,
    create_model,
    Field,
    PrivateAttr,
    field_validator,
    model_validator,
    ValidationInfo,
    ValidationError
)


from fastapi import Query

from stac_pydantic.shared import BBox
from stac_pydantic.api import Search

from stac_fastapi.types.search import (
    str2list,
    str2bbox
)

import cql2

from stac_fastapi.static.core import (
    WalkMarker,
)

from stac_fastapi.api.models import (
    create_request_model,
    ItemCollectionUri as _LegacyBaseSearchCollectionItems,
    BaseSearchGetRequest as LegacyBaseSearchItems,
    APIRequest as LegacyBaseModel,
    DatetimeMixin as LegacyDatetimeMixin,
)

_filter_example = {
    "op": "and",
    "args": [
        {
            "op": "=",
            "args": [
                {"property": "id"},
                "LC08_L1TP_060247_20180905_20180912_01_T1_L1TP",
            ],
        },
        {"op": "=", "args": [{"property": "collection"}, "landsat8_l1tp"]},
    ],
},


class PaginationExtension(BaseModel):
    token: Optional[str] = None

    _walk_marker: Optional[WalkMarker] = PrivateAttr(default=None)

    @property
    def walk_marker(self) -> Optional[WalkMarker]:
        return self._walk_marker

    @field_validator("token", mode="after")
    @classmethod
    def validate_token(
        cls, value: Optional[str], info: ValidationInfo
    ) -> Optional[str]:
        if value is not None:
            info.data["_walk_marker"] = WalkMarker.from_str(value)

        return value


class FilterExtension(BaseModel):
    filter: Annotated[Optional[Dict | str], Field(
        default=None,
        description="A CQL2 filter expression for filtering items.",
        json_schema_extra={
            "example": _filter_example
        },
    )] = None
    filter_lang: Optional[Literal["cql2-json"] | Literal["cql2-text"]] = Field(
        "cql2-json",
        alias="filter-lang",
        description="The CQL filter encoding that the 'filter' value uses.",
    )

    @model_validator(mode='before')
    @classmethod
    def validate_filter(cls, data: Any) -> Any:
        if not isinstance(data, Dict):
            return data

        filter_lang = data.get("filter-lang", "cql2-json")
        filter_expr = data.get("filter", None)

        if filter_lang not in ["cql2-json", "cql2-text"]:
            return data

        if filter_lang == "cql2-json" and isinstance(filter_expr, str):
            filter_expr = orjson.loads(filter_expr)

        if filter_expr is not None:
            try:
                cql2.Expr(filter_expr)
            except (ValueError, TypeError, cql2.ValidationError) as error:
                raise ValidationError(
                    f"{json.dumps(filter_expr)[:24]}... is not a valid CQL2 json expression : {str(error)}"
                ) from error

        data["filter-lang"] = filter_lang
        data["filter"] = filter_expr

        return data


class SearchItems(Search, PaginationExtension, FilterExtension):
    pass


class SearchCollections(Search, PaginationExtension, FilterExtension):
    collections: ClassVar[None]
    ids: ClassVar[None]

    intersects: ClassVar[None]


class SearchCollectionItems(Search, PaginationExtension, FilterExtension):
    collections: ClassVar[None]
    ids: ClassVar[None]

    collection_id: str


def make_legacy(model: Type[BaseModel]):

    class legacy_model(LegacyBaseModel):

        _model: BaseModel

        def __init__(self, **kwargs):
            self._model = model(**kwargs)

        def args(self):
            return self._model

        def kwargs(self):
            return {
                **self._model.model_dump(),
                # "query": self._model
            }

    return legacy_model


LegacySearchItems = make_legacy(SearchItems)
LegacySearchCollections = make_legacy(SearchCollections)
LegacySearchCollectionItems = make_legacy(SearchCollectionItems)
