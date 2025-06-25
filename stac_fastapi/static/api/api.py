from typing import (
    Annotated
)

import logging
import contextlib
import datetime as datetimelib
from os import path

import pydantic

from fastapi import FastAPI, Query
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exception_handlers import (
    http_exception_handler
)
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware import Middleware

from brotli_asgi import BrotliMiddleware

from stac_fastapi.api.app import StacApi
from stac_fastapi.api.middleware import CORSMiddleware, ProxyHeaderMiddleware
from stac_fastapi.extensions.core import (
    TokenPaginationExtension,
    CollectionSearchExtension,
    SearchFilterExtension,
    CollectionSearchFilterExtension,
    ItemCollectionFilterExtension
)
from stac_fastapi.api.models import (
    create_get_request_model,
    create_post_request_model,
    create_request_model,
    ItemCollectionUri,
    EmptyRequest
)

from requests import Session
from requests_cache import CachedSession
import xxhash
import orjson

from .config import Settings
from .core_client import CoreClient
from .filters_client import FiltersClient
from .models import (
    SearchItems,
    LegacySearchItems,
    LegacySearchCollections,
    LegacySearchCollectionItems,
)
from .middlewares import (
    TimeoutMiddleware,
    ProfileMiddleware
)
from .config import (
    Settings
)

from stac_fastapi.static.core.requests import (
    FileSession,
    is_file_uri,
    file_uri_to_file_path
)

from stac_fastapi.types.search import (
    BaseSearchGetRequest,
    BaseSearchPostRequest
)

logger = logging.getLogger(__name__)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):

    settings: Settings = app.state.settings

    if is_file_uri(settings.catalog_href):
        app.state.session = FileSession()
        app.state.catalog_is_file = True
        app.mount("/", StaticFiles(directory=file_uri_to_file_path(path.dirname(settings.catalog_href))), name="static")
    elif not settings.cache:
        app.state.session = Session()
        app.state.catalog_is_file = False
    else:
        app.state.session = CachedSession(
            backend="filesystem",
            cache_control=True,
            expire_after=datetimelib.timedelta(hours=1),
            stale_if_error=False,
            stale_while_revalidate=False,
            # backend options : https://requests-cache.readthedocs.io/en/stable/modules/requests_cache.backends.filesystem.html
            cache_name=f"stac_api_cache_{xxhash.xxh3_128_hexdigest(settings.catalog_href)}",
            use_temp=True
        )
        app.state.catalog_is_file = False

    yield

    app.state.session.close()


def make_api(settings: Settings):
    extensions = []

    # /search extensions
    extensions.extend(search_extensions := [
        TokenPaginationExtension(),
        SearchFilterExtension(client=FiltersClient())
    ])

    # /collections extensions
    extensions.append(collection_search_extension := CollectionSearchExtension.from_extensions([
        TokenPaginationExtension(),
        CollectionSearchFilterExtension(client=FiltersClient())
    ]))

    # /collections/{collectionId}/items extensions
    extensions.extend(collections_items_extensions := [
        TokenPaginationExtension(),
        ItemCollectionFilterExtension(client=FiltersClient())
    ])

    api = StacApi(
        app=FastAPI(
            openapi_url=settings.openapi_url,
            docs_url=settings.docs_url,
            redoc_url=None,
            root_path=settings.root_path,
            title=settings.stac_fastapi_title,
            version=settings.stac_fastapi_version,
            description=settings.stac_fastapi_description,
            lifespan=lifespan
        ),
        settings=settings,
        extensions=extensions,
        client=CoreClient(),
        response_class=ORJSONResponse,
        # search_post_request_model=create_post_request_model(search_extensions),
        search_post_request_model=SearchItems,
        search_get_request_model=create_get_request_model(search_extensions),
        items_get_request_model=create_request_model(
            model_name="ItemCollectionUri",
            base_model=ItemCollectionUri,
            extensions=collections_items_extensions,
            request_type="GET",
        ),
        collections_get_request_model=create_get_request_model([collection_search_extension]),
        # search_post_request_model=object,
        # search_get_request_model=EmptyRequest,
        # items_get_request_model=EmptyRequest,
        # collections_get_request_model=EmptyRequest,
        middlewares=[
            Middleware(BrotliMiddleware),
            Middleware(ProxyHeaderMiddleware),
            Middleware(
                CORSMiddleware,
                allow_origins=settings.cors_origins,
                allow_methods=settings.cors_methods,
            ),
            Middleware(TimeoutMiddleware),
            Middleware(ProfileMiddleware, settings)
        ],
    )

    if settings.log_level == "debug":
        logger.warning("Security Warning : With log_level set to 'debug' errors are sent to clients with detailed context")

        async def safe_http_exception_handler(request, error: StarletteHTTPException):
            if isinstance(error, StarletteHTTPException):
                if isinstance(error.detail, pydantic.ValidationError):
                    error.detail = error.detail.json(
                        include_context=True,
                        include_url=False,
                        include_input=True
                    )
                elif error.detail is not None:
                    try:
                        orjson.dumps(error.detail)
                    except Exception:
                        error.detail = str(error.detail)

            return await http_exception_handler(request, error)

    else:
        async def safe_http_exception_handler(request, error: StarletteHTTPException):
            if isinstance(error, StarletteHTTPException) and isinstance(error.detail, Exception):
                error.detail = str(error.detail)

            return await http_exception_handler(request, error)

    api.app.exception_handler(StarletteHTTPException)(safe_http_exception_handler)

    return api
