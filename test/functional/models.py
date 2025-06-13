from typing import (
    Optional,
    Dict
)

from urllib.parse import urlparse
import json

import pystac

from stac_pydantic import Item, Collection, ItemCollection
from stac_pydantic.links import Links


def normalize_href(href: str, base_url: Optional[str] = None) -> str:
    # if base_url:
    #     if href.startswith(base_url):
    #         return href[len(base_url):]
    # else:
    #     return urlparse(href).path

    return href


def validate_item(item: str | Item | pystac.Item | Dict) -> pystac.Item:

    if isinstance(item, str):
        try:
            item = json.loads(item)
        except json.JSONDecodeError as error:
            raise ValueError("Malformed Item JSON") from error

        item = pystac.Item.from_dict(item)
    elif isinstance(item, Item):
        item = pystac.Item.from_dict(item.model_dump())
    elif isinstance(item, Dict):
        item = pystac.Item.from_dict(item)
    elif not isinstance(item, pystac.Item):
        raise TypeError(f"Unexpected 'Item' object type : {type(item)}")

    return item


def normalize_item(item: pystac.Item, base_url: Optional[str] = None) -> pystac.Item:
    item = item.clone()
    item.links = [link for link in item.links if link.rel not in ["self", "root", "parent"]]

    for link in item.links:
        link.href = normalize_href(link.href, base_url)

    for asset in item.assets.values():
        asset.href = normalize_href(asset.href, base_url)

    return item


def validate_collection(collection: str | Dict | Collection | pystac.Collection) -> pystac.Collection:

    if isinstance(collection, str):
        try:
            collection = json.loads(collection)
        except json.JSONDecodeError as error:
            raise ValueError("Malformed Collection JSON") from error

        collection = pystac.Collection.from_dict(collection)
    elif isinstance(collection, Collection):
        collection = pystac.Collection.from_dict(collection.model_dump())
    elif isinstance(collection, Dict):
        collection = pystac.Collection.from_dict(collection)
    elif not isinstance(collection, pystac.Collection):
        raise TypeError(f"Unexpected 'Collection' object type : {type(collection)}")

    return collection


def normalize_collection(collection: pystac.Collection, base_url: Optional[str] = None) -> pystac.Collection:
    collection = collection.clone()
    collection.links = [link for link in collection.links if link.rel not in ["self", "root", "parent"]]

    for link in collection.links:
        link.href = normalize_href(link.href, base_url)

    for asset in collection.assets.values():
        asset.href = normalize_href(asset.href, base_url)

    return collection


def validate_item_collection(item_collection: str | Dict | Item | pystac.ItemCollection) -> pystac.ItemCollection:

    if isinstance(item_collection, str):
        try:
            item_collection = json.loads(item_collection)
        except json.JSONDecodeError as error:
            raise ValueError("Malformed ItemCollection JSON") from error

        item_collection = pystac.ItemCollection.from_dict(item_collection)
    elif isinstance(item_collection, ItemCollection):
        item_collection = pystac.ItemCollection.from_dict(item_collection.model_dump())
    elif isinstance(item_collection, Dict):
        item_collection = pystac.ItemCollection.from_dict(item_collection)
    elif not isinstance(item_collection, pystac.ItemCollection):
        raise TypeError(f"Unexpected 'ItemCollection' object type : {type(item_collection)}")

    return item_collection
