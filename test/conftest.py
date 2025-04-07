from typing import (
    NamedTuple,
    Any
)
import datetime as datetimelib
import logging
import os
from os import path
import time
from urllib.parse import urlparse, urljoin
import json

import pytest
import pystac
from fastapi.testclient import TestClient as Client

from stac_test_tools import (
    TestCatalog,
    get_items,
    get_collections
)

from stac_fastapi.static.api import make_api
from stac_fastapi.static.api import Settings
from stac_fastapi.api.app import StacApi

from stac_pydantic.item import Item
from stac_pydantic.item_collection import ItemCollection
from stac_pydantic.collection import Collection
from stac_pydantic.catalog import Catalog

logger = logging.getLogger(__file__)


class rfc3339:

    @classmethod
    def datetime_to_str(cls, datetime: datetimelib.datetime | tuple[datetimelib.datetime | None, datetimelib.datetime | None]) -> str:
        if datetime is None:
            datetime_str = ""
        elif isinstance(datetime, datetimelib.datetime):
            datetime_str = datetime.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        elif datetime == (None, None):
            datetime_str = ""
        elif datetime[0] == None:
            datetime_str = f"../{cls.datetime_to_str(datetime[1])}"
        elif datetime[1] == None:
            datetime_str = f"{cls.datetime_to_str(datetime[0])}/.."
        elif datetime[0] == datetime[1]:
            datetime_str = cls.datetime_to_str(datetime[1])
        else:
            datetime_str = f"{cls.datetime_to_str(datetime[0])}/{cls.datetime_to_str(datetime[1])}"

        return datetime_str


def test_catalog():
    catalog_href = os.getenv("catalog_href", None)
    n_items = int(os.getenv("n_items", "1000"))
    start = time.time()

    i_items = 0
    i_others = 0
    for generated_object in (test_catalog := TestCatalog.generate(catalog_href=catalog_href, n_items=n_items)):
        if isinstance(generated_object, pystac.Item):
            i_items += 1
        else:
            i_others += 1

        logger.info(
            f"\rGenerating catalog : {i_items}(/{n_items}) items + {i_others}(/?) collections", end="")

    if i_items or i_others:
        logger.info(f"Catalog instanciated in {time.time() - start}s")

    return test_catalog.result


@pytest.fixture(scope="package", name="test_catalog")
def _test_catalog():
    return test_catalog()


class TestContextTuple(NamedTuple):
    __test__ = False

    api: StacApi
    test_catalog: TestCatalog


@pytest.fixture
def test_context(test_catalog: TestCatalog) -> TestContextTuple:
    # catalog_href = os.getenv("catalog_href", "file://" + test_catalog.catalog_href)
    catalog_href = "file://" + test_catalog.catalog_href

    return TestContextTuple(
        api=make_api(Settings(
            catalog_href=catalog_href
        )),
        test_catalog=test_catalog
    )


class BaseTestAPI():

    client: Client
    test_catalog: TestCatalog

    @pytest.fixture(autouse=True)
    def _init_test_context(self, test_context: TestContextTuple):
        with Client(test_context.api.app) as client:
            self.client = client
            self.test_catalog = test_context.test_catalog

            yield

    def _canonize_href(self, href: str):
        if urlparse(href, scheme="file").scheme == "file":
            return "/" + path.relpath(
                href,
                path.dirname(self.test_catalog.catalog_href)
            )
        else:
            return urlparse(href).path

    def _validate_item(self, item: str | Any | Item | pystac.Item):
        if isinstance(item, str):
            validated_item = pystac.Item.from_dict(
                # Item.model_validate_json(item).model_dump()
                json.loads(Item.model_validate_json(item).model_dump_json())
            )
        elif isinstance(item, Item):
            validated_item = pystac.Item.from_dict(
                # item.model_dump()
                json.loads(item.model_dump_json())
            )
        elif isinstance(item, pystac.Item):
            validated_item = item
        else:
            validated_item = pystac.Item.from_dict(
                # Item.model_validate(item).model_dump()
                json.loads(Item.model_validate(item).model_dump_json())
            )

        cataloged_item = self.test_catalog.get_item(validated_item.id)

        assert cataloged_item is not None

        assert self._canonize_href(cataloged_item.get_self_href(
        )) == self._canonize_href(validated_item.get_self_href())

        assert sorted([
            self._canonize_href(urljoin(cataloged_item.get_self_href(), link.get_href(transform_href=False)))
            for link
            in cataloged_item.links
        ]) == sorted([
            self._canonize_href(link.get_href(transform_href=False))
            for link
            in validated_item.links
        ])

        assert sorted([
            self._canonize_href(urljoin(cataloged_item.get_self_href(), asset.href))
            for asset
            in (cataloged_item.assets or {}).values()
        ]) == sorted([
            self._canonize_href(asset.href)
            for asset
            in (validated_item.assets or {}).values()
        ])

        return Item.model_validate(
            validated_item.to_dict(transform_hrefs=False)
        )

    def _validate_item_collection(self, item_collection: str | Any) -> ItemCollection:
        if isinstance(item_collection, str):
            validated_item_collection = ItemCollection.model_validate_json(item_collection)
        elif isinstance(item_collection, ItemCollection):
            validated_item_collection = item_collection
        else:
            validated_item_collection = ItemCollection.model_validate(item_collection)

        for item in validated_item_collection.features:
            self._validate_item(item)

        return validated_item_collection

    def _validate_collection(self, collection: str | Any) -> Collection:
        if isinstance(collection, str):
            validated_collection = pystac.Collection.from_dict(
                # Collection.model_validate_json(collection).model_dump()
                json.loads(Collection.model_validate_json(collection).model_dump_json())
            )
        elif isinstance(collection, Collection):
            validated_collection = pystac.Collection.from_dict(
                # collection.model_dump()
                json.loads(collection.model_dump_json())
            )
        elif isinstance(collection, pystac.Collection):
            validated_collection = collection
        else:
            collection["assets"] = collection.get("assets", {})
            validated_collection = pystac.Collection.from_dict(
                # Collection.model_validate(collection).model_dump()
                json.loads(Collection.model_validate(collection).model_dump_json())
            )

        cataloged_collection = self.test_catalog.get_collection(validated_collection.id)

        assert cataloged_collection is not None

        assert sorted([
            self._canonize_href(urljoin(cataloged_collection.get_self_href(), link.get_href(transform_href=False)))
            for link
            in cataloged_collection.links
        ]) == sorted([
            self._canonize_href(link.get_href(transform_href=False))
            for link
            in validated_collection.links
        ])

        assert sorted([
            self._canonize_href(urljoin(cataloged_collection.get_self_href(), asset.href))
            for asset
            in (cataloged_collection.assets or {}).values()
        ]) == sorted([
            self._canonize_href(asset.href)
            for asset
            in (validated_collection.assets or {}).values()
        ])

        return Collection.model_validate(
            validated_collection.to_dict(transform_hrefs=False)
        )

    def _validate_catalog(self, catalog: str | Any) -> Catalog:
        if isinstance(catalog, str):
            validated_catalog = pystac.Catalog.from_dict(
                json.loads(Catalog.model_validate_json(catalog).model_dump_json())
            )
        elif isinstance(catalog, Catalog):
            validated_catalog = pystac.Catalog.from_dict(
                json.loads(catalog.model_dump_json())
            )
        elif isinstance(catalog, pystac.Catalog):
            validated_catalog = catalog
        else:
            validated_catalog = pystac.Catalog.from_dict(
                json.loads(Catalog.model_validate(catalog).model_dump_json())
            )

        return Catalog.model_validate(
            validated_catalog.to_dict(transform_hrefs=False)
        )
