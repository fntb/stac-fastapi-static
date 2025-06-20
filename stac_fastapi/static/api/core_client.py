from typing import (
    List,
    Optional,
    Type,
    Callable,
    TypeVar,
    Any,
    cast,
    Dict
)

from os import path
from urllib.parse import urljoin

import orjson
from orjson import JSONDecodeError

from fastapi import Request, HTTPException

from stac_pydantic.shared import MimeTypes
from stac_pydantic.item import Item
from stac_pydantic.collection import Collection
from stac_pydantic.catalog import Catalog
from stac_pydantic.item_collection import ItemCollection

from stac_fastapi.types import stac
from stac_fastapi.types.core import Relations, BaseCoreClient
from stac_fastapi.types.requests import get_base_url

from pydantic import BaseModel, ValidationError

from .config import Settings

from stac_fastapi.static.core import (
    WalkResult,
    walk_collections,
    make_filter_depth,
    BadStacObjectFilterError,
    BadWalkResultError,
    WalkFilter
)

from stac_fastapi.static.core.requests import (
    Session,
    file_uri_to_file_path,
    is_file_uri
)

from stac_fastapi.static.core.client import (
    search_items as _search_items,
    search_collections as _search_collections,
    search_collection_items as _search_collection_items,
    get_collection as _get_collection,
    get_item as _get_item,
    CollectionNotFoundError
)

from .models import (
    SearchItems,
    SearchCollections,
    SearchCollectionItems
)

from .links import LinksBuilder


def wrap_error(type: Type[BaseException] | tuple[Type[BaseException]], status_code: int = 500):

    WrappedCallable = TypeVar("WrappedCallable", bound=Callable[..., Any])

    def wrap_error(func: WrappedCallable) -> WrappedCallable:
        def wrapped_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except type as error:
                raise HTTPException(status_code=status_code, detail=error) from error

        return cast(WrappedCallable, wrapped_func)

    return wrap_error


search_items = wrap_error(BadStacObjectFilterError, status_code=400)(_search_items)
search_collections = wrap_error(BadStacObjectFilterError, status_code=400)(_search_collections)
search_collection_items = wrap_error(BadStacObjectFilterError, status_code=400)(_search_collection_items)
get_collection = wrap_error(BadStacObjectFilterError, status_code=400)(_get_collection)
get_item = wrap_error(BadStacObjectFilterError, status_code=400)(_get_item)


@wrap_error(BadWalkResultError, status_code=500)
def resolve(
    result: WalkResult,
    *,
    base_api_href: str,
    catalog_is_file: bool = True,
    catalog_href: bool = True,
    pre_resolve: Optional[Callable[[Catalog | Collection | Item], None]] = None
) -> Catalog | Collection | Item:
    object: Catalog | Collection | Item = result.resolve()

    # if isinstance(object, Item):
    #     object.properties.walk_path = str(result.walk_path)

    if pre_resolve is not None:
        pre_resolve(object)

    if catalog_is_file:
        catalog_dir = path.dirname(file_uri_to_file_path(catalog_href))

        for link in object.links.link_iterator():
            if is_file_uri(link.href):
                link.href = urljoin(
                    base_api_href,
                    path.relpath(
                        file_uri_to_file_path(link.href),
                        catalog_dir
                    )
                )
            link.title = link.title if link.title is not None else link.rel.capitalize()

        if isinstance(object, (Item, Collection)) and object.assets is not None:
            for asset in object.assets.values():
                if is_file_uri(asset.href):
                    asset.href = urljoin(
                        base_api_href,
                        path.relpath(
                            file_uri_to_file_path(asset.href),
                            catalog_dir
                        )
                    )

    return object


class CoreClient(BaseCoreClient):

    def landing_page(self, request: Request, **kwargs):
        """Landing page.

        Called with `GET /`.

        Returns:
            API landing page, serving as an entry point to the API.
        """
        settings: Settings = request.app.state.settings
        session: Session = request.app.state.session
        base_url = get_base_url(request)

        landing_page = self._landing_page(
            base_url=base_url,
            conformance_classes=self.conformance_classes(),
            extension_schemas=[],
        )

        landing_page["links"].extend([
            {
                "rel": Relations.queryables.value,
                "type": MimeTypes.jsonschema.value,
                "title": "Queryables",
                "href": urljoin(base_url, "queryables"),
            },
            {
                "rel": Relations.service_desc.value,
                "type": MimeTypes.openapi.value,
                "title": "OpenAPI service description",
                "href": str(request.url_for("openapi")),
            },
            {
                "rel": Relations.service_doc.value,
                "type": MimeTypes.html.value,
                "title": "OpenAPI service documentation",
                "href": str(request.url_for("swagger_ui_html")),
            }
        ])

        landing_page["links"].extend([
            {
                "rel": Relations.child.value,
                "type": MimeTypes.json.value,
                "title": walk_result.resolve().title or walk_result.resolve().id,
                "href": urljoin(base_url, f"collections/{walk_result.resolve().id}"),
            }
            for walk_result
            in WalkFilter(
                walk_collections(
                    settings.catalog_href,
                    session=session,
                    settings=settings
                ),
                make_filter_depth(depth=settings.landing_page_child_collections_max_depth)
            )
        ])

        return landing_page

    def _search(
        self,
        request: Request,
        query: SearchItems
    ) -> stac.ItemCollection:
        settings: Settings = request.app.state.settings
        session: Session = request.app.state.session
        catalog_is_file: bool = request.app.state.catalog_is_file
        base_api_href = get_base_url(request)

        page = search_items(
            collections=query.collections,
            ids=query.ids,
            bbox=query.bbox,
            intersects=query.intersects,
            datetime=(query.start_date, query.end_date),
            walk_marker=query.walk_marker,
            limit=query.limit,
            filter=query.filter,
            settings=settings,
            session=session
        )

        return ItemCollection(
            type="FeatureCollection",
            features=[
                resolve(
                    walk_result,
                    base_api_href=base_api_href,
                    catalog_is_file=catalog_is_file,
                    catalog_href=settings.catalog_href
                )
                for walk_result
                in page.page
            ],
            links=LinksBuilder().build_self_link(
                request
            ).build_root_link(
                request
            ).build_pagination_links(request, page).links
        ).model_dump()

    def post_search(
        self,
        kwargs: SearchItems,
        request: Request,
        **_kwargs
    ) -> stac.ItemCollection:
        """Cross catalog search (POST).

        Called with `POST /search`.

        Args:
            search_request: search request parameters.

        Returns:
            ItemCollection containing items which match the search criteria.
        """

        return self._search(
            request=request,
            query=kwargs
        )

    def get_search(
        self,
        request: Request,
        **kwargs,
    ) -> stac.ItemCollection:
        """Cross catalog search (GET).

        Called with `GET /search`.

        Returns:
            ItemCollection containing items which match the search criteria.
        """

        try:
            query = SearchItems(
                filter=kwargs["filter_expr"],
                **{
                    "filter-lang": kwargs["filter_lang"]
                },
                token=kwargs["token"],
                collections=kwargs["collections"],
                ids=kwargs["ids"],
                bbox=kwargs["bbox"],
                intersects=orjson.loads(kwargs["intersects"]) if kwargs["intersects"] else None,
                datetime=kwargs["datetime"],
                limit=kwargs["limit"],
            )
        except (ValidationError, JSONDecodeError) as error:
            raise HTTPException(status_code=400, detail=error) from error

        return self._search(
            request=request,
            query=query
        )

    def get_item(self, request: Request, item_id: str, collection_id: str, **kwargs) -> stac.Item:
        """Get item by id.

        Called with `GET /collections/{collection_id}/items/{item_id}`.

        Args:
            item_id: Id of the item.
            collection_id: Id of the collection.

        Returns:
            Item.
        """
        settings: Settings = request.app.state.settings
        session: Session = request.app.state.session
        catalog_is_file: bool = request.app.state.catalog_is_file
        base_api_href = get_base_url(request)

        item_walk_result = get_item(
            item_id=item_id,
            collection_id=collection_id,
            settings=settings,
            session=session
        )

        if not item_walk_result:
            raise HTTPException(status_code=404, detail=f"Item {item_id} not found.")
        else:
            return resolve(
                item_walk_result,
                base_api_href=base_api_href,
                catalog_is_file=catalog_is_file,
                catalog_href=settings.catalog_href
            ).model_dump()

    def all_collections(
        self,
        request: Request,
        **kwargs
    ) -> stac.Collections:
        """Get all available collections.

        Called with `GET /collections`.

        Returns:
            A list of collections.
        """
        settings: Settings = request.app.state.settings
        session: Session = request.app.state.session
        catalog_is_file: bool = request.app.state.catalog_is_file
        base_api_href = get_base_url(request)

        try:
            query = SearchCollections(
                filter=kwargs["filter_expr"],
                **{
                    "filter-lang": kwargs["filter_lang"]
                },
                token=kwargs["token"],
                bbox=kwargs["bbox"],
                datetime=kwargs["datetime"],
                limit=kwargs["limit"]
            )
        except (ValidationError, JSONDecodeError) as error:
            raise HTTPException(status_code=400, detail=error) from error

        page = search_collections(
            walk_marker=query.walk_marker,
            limit=query.limit,
            bbox=query.bbox,
            datetime=(query.start_date, query.end_date),
            filter=query.filter,
            session=session,
            settings=settings
        )

        return {
            "collections": [
                collection.model_dump()
                for collection
                in [
                    resolve(
                        walk_result,
                        base_api_href=base_api_href,
                        catalog_is_file=catalog_is_file,
                        catalog_href=settings.catalog_href,
                        pre_resolve=lambda collection: collection.links.append(
                            LinksBuilder().build_queryables_link(request, collection_id=collection.id)._links[0]
                        )
                    )
                    for walk_result
                    in page.page
                ]
            ],
            "links": LinksBuilder().build_self_link(
                request
            ).build_root_link(
                request
            ).build_pagination_links(request, page).links
        }

    def get_collection(
        self,
        request: Request,
        collection_id: str,
        **kwargs
    ) -> stac.Collection:
        """Get collection by id.

        Called with `GET /collections/{collection_id}`.

        Args:
            collection_id: Id of the collection.

        Returns:
            Collection.
        """
        settings: Settings = request.app.state.settings
        session: Session = request.app.state.session
        catalog_is_file: bool = request.app.state.catalog_is_file
        base_api_href = get_base_url(request)

        collection_walk_result = get_collection(
            collection_id=collection_id,
            settings=settings,
            session=session
        )

        if not collection_walk_result:
            raise HTTPException(status_code=404, detail=f"Collection {collection_id} not found.")
        else:
            return resolve(
                collection_walk_result,
                base_api_href=base_api_href,
                catalog_is_file=catalog_is_file,
                catalog_href=settings.catalog_href
            ).model_dump()

    def item_collection(
        self,
        request: Request,
        **kwargs,
    ) -> stac.ItemCollection:
        """Get all items from a specific collection.

        Called with `GET /collections/{collection_id}/items`

        Args:
            collection_id: id of the collection.
            limit: number of items to return.
            token: pagination token.

        Returns:
            An ItemCollection.
        """
        settings: Settings = request.app.state.settings
        session: Session = request.app.state.session
        catalog_is_file: bool = request.app.state.catalog_is_file
        base_api_href = get_base_url(request)

        try:
            query = SearchCollectionItems(
                filter=kwargs["filter_expr"],
                **{
                    "filter-lang": kwargs["filter_lang"]
                },
                token=kwargs["token"],
                bbox=kwargs["bbox"],
                datetime=kwargs["datetime"],
                limit=kwargs["limit"],
                collection_id=kwargs["collection_id"]
            )
        except (ValidationError, JSONDecodeError) as error:
            raise HTTPException(status_code=400, detail=error) from error

        try:
            page = search_collection_items(
                collection_id=query.collection_id,
                bbox=query.bbox,
                intersects=None,
                datetime=query.datetime,
                limit=query.limit,
                walk_marker=query.walk_marker,
                filter=query.filter,
                session=session,
                settings=settings,
            )
        except CollectionNotFoundError as error:
            raise HTTPException(status_code=404, detail=f"Collection {query.collection_id} not found.") from error

        return ItemCollection(
            type="FeatureCollection",
            features=[
                resolve(
                    walk_result,
                    base_api_href=base_api_href,
                    catalog_is_file=catalog_is_file,
                    catalog_href=settings.catalog_href,
                )
                for walk_result
                in page.page
            ],
            links=LinksBuilder().build_self_link(
                request
            ).build_root_link(
                request
            ).build_pagination_links(request, page).links
        ).model_dump()
