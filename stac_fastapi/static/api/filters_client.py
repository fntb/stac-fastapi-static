from typing import (
    Any,
    Optional
)

from fastapi import Request
from stac_fastapi.extensions.core.filter.client import AsyncBaseFiltersClient


class FiltersClient(AsyncBaseFiltersClient):

    async def get_queryables(
        self,
        request: Request,
        collection_id: Optional[str] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:

        return {
            "$schema": "https://json-schema.org/draft/2019-09/schema",
            "$id": str(request.url),
            "type": "object",
            # "title": "Queryables for Example STAC API",
            # "description": "Queryable names for the example STAC API Item Search filter.",
            "properties": {},
            "additionalProperties": True
        }
