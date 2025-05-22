from typing import (
    List,
    Dict,
    Optional
)

from typing_extensions import (
    Self
)

from urllib.parse import urljoin

from fastapi import Request, HTTPException

from stac_pydantic.shared import MimeTypes
from stac_pydantic.links import Link

from stac_fastapi.types.core import Relations
from stac_fastapi.types.requests import get_base_url

from stac_fastapi.static.core import (
    WalkPage
)


class LinksBuilder():
    _links: list[Link]

    def __init__(self):
        self._links = []

    @property
    def links(self) -> List[Dict]:
        return [
            link.model_dump()
            for link
            in self._links
        ]

    def build_self_link(self, request: Request) -> Self:
        self._links.append(
            Link(
                href=str(request.url),
                rel=Relations.self.value,
                type=MimeTypes.json
            )
        )

        return self

    def build_root_link(self, request: Request) -> Self:
        self._links.append(
            Link(
                href=get_base_url(request),
                rel=Relations.root.value,
                type=MimeTypes.json
            )
        )

        return self

    def build_pagination_links(self, request: Request, page: WalkPage) -> Self:
        links = []

        if page.prev:
            link = {
                "rel": Relations.previous.value,
                "type": MimeTypes.geojson,
                "method": request.method,
            }

            if request.method == "GET":
                link["href"] = str(request.url.replace_query_params(token=str(page.prev)))
            elif request.method == "POST":
                link["href"] = str(request.url)
                link["body"] = {
                    **request._json,
                    "token": str(page.prev)
                }

            links.append(link)

        if page.next:
            link = {
                "rel": Relations.next.value,
                "type": MimeTypes.geojson,
                "method": request.method,
            }

            if request.method == "GET":
                link["href"] = str(request.url.replace_query_params(token=str(page.next)))
            elif request.method == "POST":
                link["href"] = str(request.url)
                link["body"] = {
                    **request._json,
                    "token": str(page.next)
                }

            links.append(link)

        self._links.extend([
            Link(**link)
            for link
            in links
        ])

        return self

    def build_queryables_link(self, request: Request, collection_id: Optional[str] = None) -> Self:
        base_url = get_base_url(request)

        self._links.append(
            Link(
                rel=Relations.queryables.value,
                type=MimeTypes.jsonschema,
                title="Queryables",
                href=urljoin(
                    base_url,
                    f"collections/{collection_id}/queryables"
                ) if collection_id else urljoin(
                    base_url,
                    f"search/queryables"
                ),
            )
        )

        return self
