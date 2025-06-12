
import pytest

from typing import (
    List,
    Dict,
    Optional,
    Any,
)

from typing_extensions import (
    TypedDict
)

from urllib.parse import urljoin
import requests
import pystac


from stac_pydantic.collection import Collection
from pydantic import TypeAdapter

from .models import (
    validate_item_collection,
    validate_collection,
    validate_item
)

from ..catalog_tools import (
    pick_item,
    pick_collection
)


class Collections(TypedDict, total=False):
    """All collections endpoint.
    https://github.com/radiantearth/stac-api-spec/tree/master/collections
    """

    collections: List[Collection]
    links: List[Dict[str, Any]]
    numberMatched: Optional[int] = None
    numberReturned: Optional[int] = None


def test_get_item_search_response_model(api_base_href: str):
    response = requests.get(urljoin(api_base_href, "/search"))

    response.raise_for_status()

    validate_item_collection(response.json())


def test_post_item_search_response_model(api_base_href: str):
    response = requests.post(urljoin(api_base_href, "/search"))

    response.raise_for_status()

    validate_item_collection(response.json())


def test_item_response_model(api_base_href: str, catalog: pystac.Catalog):
    item = pick_item(catalog)
    collection = item.get_parent()

    response = requests.get(urljoin(api_base_href, f"/collections/{collection.id}/items/{item.id}"))

    response.raise_for_status()

    validate_item(response.json())


def test_all_collections_response_model(api_base_href: str):
    request_href = "/collections"

    response = requests.get(urljoin(api_base_href, request_href))

    response.raise_for_status()

    TypeAdapter(Collections).validate_json(response.text)


def test_collection_response_model(api_base_href: str, catalog: pystac.Catalog):
    collection = pick_collection(catalog)

    request_href = f"/collections/{collection.id}"
    response = requests.get(urljoin(api_base_href, request_href))

    response.raise_for_status()

    validate_collection(response.json())


def test_collection_items_response_model(api_base_href: str, catalog: pystac.Catalog):
    collection = pick_collection(catalog)

    request_href = f"/collections/{collection.id}/items"
    response = requests.get(urljoin(api_base_href, request_href))

    response.raise_for_status()

    validate_item_collection(response.json())


def test_base_queryables_response_model(api_base_href: str):
    request_href = "/queryables"
    response = requests.get(urljoin(api_base_href, request_href))

    response.raise_for_status()

    response_json = response.json()
    assert response_json["$id"].endswith("/queryables")
    assert response_json["type"] == "object"
    assert "properties" in response_json


def test_collection_queryables_response_model(api_base_href: str, catalog: pystac.Catalog):
    collection = pick_collection(catalog)

    request_href = f"/collections/{collection.id}/queryables"
    response = requests.get(urljoin(api_base_href, request_href))

    response.raise_for_status()

    response_json = response.json()
    assert response_json["$id"].endswith("/queryables")
    assert response_json["type"] == "object"
    assert "properties" in response_json
