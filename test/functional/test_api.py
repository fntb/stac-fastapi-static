
# import pytest

# from typing import (
#     List,
#     Dict,
#     Optional,
#     Any,
#     NamedTuple
# )

# from typing_extensions import (
#     TypedDict
# )

# from functools import cache

# from urllib.parse import urlparse, parse_qs
# import json

# import shapely

# from stac_pydantic.collection import Collection
# from stac_pydantic.item import Item
# from stac_pydantic.links import Link
# from stac_pydantic.item_collection import ItemCollection
# from pydantic import TypeAdapter
# from stac_fastapi.static.core import WalkPath

# from httpx import Response

# from stac_fastapi.static.core.walk_filters.temporal_filters import make_match_datetime
# from stac_fastapi.static.core.walk_filters.spatial_filters import (
#     make_match_bbox,
#     make_match_geometry
# )
# from stac_fastapi.static.core.walk_filters.cql2_filter import (
#     make_match_item_cql2,
# )

# from ..conftest import (
#     rfc3339,
#     get_items,
#     BaseTestAPI
# )


# class Collections(TypedDict, total=False):
#     """All collections endpoint.
#     https://github.com/radiantearth/stac-api-spec/tree/master/collections
#     """

#     collections: List[Collection]
#     links: List[Dict[str, Any]]
#     numberMatched: Optional[int] = None
#     numberReturned: Optional[int] = None


# def get_next_link(links: list[Link]) -> str | None:
#     for link in links:
#         if link.rel == "next":
#             return link.href

#     return None


# def get_prev_link(links: list[Link]) -> str | None:
#     for link in links:
#         if link.rel == "prev":
#             return link.href

#     return None


# class TestCatalog(BaseTestAPI):

#     def test_static_catalog_response_model(self):
#         response = self.client.get("/catalog.json")

#         assert response.status_code == 200, "/catalog.json"
#         self._validate_catalog(response.json())


# class TestItemSearch(BaseTestAPI):

#     def _fetch(
#         self,
#         get_request_param: str,
#         post_request_body: dict,
#     ) -> List[tuple[Response, str]]:
#         responses = []

#         response = self.client.get(f"/search?{get_request_param}")
#         msg = f" -> GET /search?{get_request_param}\n <- {response.status_code}\n <- \n{response.text}"

#         responses.append((response, msg))

#         response = self.client.post("/search", json=post_request_body)
#         msg = f" -> POST /search\n ->\n" + json.dumps(post_request_body) + \
#             f"\n <- {response.status_code}\n <- \n{response.text}"

#         responses.append((response, msg))

#         return responses

#     def test_item_search_response_model(self):
#         responses = self._fetch(
#             "",
#             {}
#         )

#         for (response, msg) in responses:
#             assert response.status_code == 200, msg

#             self._validate_item_collection(response.json())

#     def test_item_search_collections_param(self):
#         collection = self.test_catalog.pick_collection()
#         collection_item_ids = set(
#             item.id
#             for item
#             in get_items(collection)
#         )

#         responses = self._fetch(
#             f"collections={collection.id}",
#             {
#                 "collections": [collection.id]
#             }
#         )

#         for (response, msg) in responses:
#             assert response.status_code == 200, msg

#             item_collection = self._validate_item_collection(response.json())

#             if len(collection_item_ids) > 0:
#                 assert len(item_collection.features) > 0, msg

#             assert set(
#                 item.id
#                 for item
#                 in item_collection.features
#             ).issubset(collection_item_ids), msg

#     def test_item_search_ids_param(self):
#         item = self.test_catalog.pick_item()

#         responses = self._fetch(
#             f"ids={item.id}",
#             {
#                 "ids": [item.id]
#             }
#         )

#         for (response, msg) in responses:
#             assert response.status_code == 200, msg

#             item_collection = self._validate_item_collection(response.json())

#             assert len(item_collection.features) == 1, msg
#             assert item_collection.features[0].id == item.id, msg

#     def test_item_search_bbox_param(self):
#         bbox = self.test_catalog.pick_bbox()

#         match_bbox = make_match_bbox(bbox)

#         bbox_str = ",".join([
#             str(coordinate)
#             for coordinate in bbox
#         ])

#         responses = self._fetch(
#             f"bbox={bbox_str}",
#             {
#                 "bbox": bbox
#             }
#         )

#         for (response, msg) in responses:
#             assert response.status_code == 200, msg

#             item_collection = self._validate_item_collection(response.json())

#             assert len(item_collection.features) > 0, msg

#             for item in item_collection.features:
#                 assert match_bbox(item), msg

#     def test_item_search_intersects_param(self):
#         geometry = self.test_catalog.pick_geometry()

#         match_geometry = make_match_geometry(geometry)

#         responses = self._fetch(
#             f"intersects={shapely.to_geojson(geometry)}",
#             {
#                 "intersects": json.loads(shapely.to_geojson(geometry))
#             }
#         )

#         for (response, msg) in responses:
#             assert response.status_code == 200, msg

#             item_collection = self._validate_item_collection(response.json())

#             assert len(item_collection.features) > 0, msg

#             for item in item_collection.features:
#                 assert match_geometry(item), msg

#     def test_item_search_datetime_param(self):
#         datetime_interval = self.test_catalog.pick_datetime_interval()

#         match_datetime = make_match_datetime(datetime_interval)

#         datetime_str = rfc3339.datetime_to_str(datetime_interval)

#         responses = self._fetch(
#             f"datetime={datetime_str}" if datetime_str else "",
#             {
#                 "datetime": datetime_str
#             } if datetime_str else {}
#         )

#         for (response, msg) in responses:
#             assert response.status_code == 200, msg

#             item_collection = self._validate_item_collection(response.json())

#             assert len(item_collection.features) > 0, msg

#             for item in item_collection.features:
#                 assert match_datetime(item), msg

#     # def test_item_search_token_param(self):

#     #     class Expectation(NamedTuple):
#     #         prev: str
#     #         next: str
#     #         item_ids: list[str]

#     #         @classmethod
#     #         @cache
#     #         def _get_ordered_item_ids():
#     #             ...

#     #         def _get_expected_item_id_from_index(item_index: int):
#     #             ...

#     #         @classmethod
#     #         def make(cls, item_index: int, page_len: int):
#     #             ...

#     #     expectations: list[Expectation] = []

#     #     page_len = 10
#     #     page_n = 5

#     #     expected_ordered_item_ids = [
#     #         item.id
#     #         for item
#     #         in self._validate_item_collection(
#     #             self.client.get(f"/search?limit={str(page_len * page_n)}").json()
#     #         ).features
#     #     ]

#     #     def get_index_token(index: int):
#     #         ...

#     #     def get_index_range_ids(start: int, end: int):
#     #         ...

#     #     pages_to_assert_as_index_ranges = [
#     #         (0, 10),
#     #         (10, 20),
#     #         (20, 30)
#     #     ]

#     #     for pages_to

#     #     def get_item_token(i: int):
#     #         response = self.client.get(f"/search?limit={str(i - 1)}").json()
#     #         item_collection = self._validate_item_collection(response.json())

#     #         href = get_next_link(item_collection.links)
#     #         query = urlparse(href).query
#     #         token = parse_qs(query)["token"][0]

#     #         return token

#     #     request_href = "/search"
#     #     ordered_item_ids = []
#     #     for i in range(page_n):
#     #         response = self.client.get(request_href).json()

#     #         assert response.status_code == 200, request_href

#     #         item_collection = self._validate_item_collection(response.json())

#     #         next_request_href = get_next_link(item_collection.links)

#     #         assert next_request_href is not None, request_href

#     #         request_href = next_request_href

#     #         break

#     #     for i in range(5):
#     #         responses = self._fetch("", {})
#     #         tokens = set(
#     #             get_next_link(response.json().links)
#     #             for (response, _)
#     #             in responses
#     #         )

#     #         assert len(tokens) == 1
#     #         token = tokens.pop()

#     #     self.client.get(f"/search").json()

#     #     self._fetch

#     #     for (response, msg) in responses:
#     #         assert response.status_code == 200, msg

#     #         item_collection = self._validate_item_collection(response.json())

#     #         assert len(item_collection.features) <= 100, msg

#     #     for (response, msg) in responses:
#     #         assert response.status_code == 200, msg

#     #     # TODO
#     #     bookmark = WalkPath.encode(*[
#     #         stac_object.get_self_href()
#     #         for stac_object
#     #         in self.test_catalog.pick_walk()
#     #     ])
#     #     token = f"next:{str(bookmark)}"

#     #     responses = self._fetch(
#     #         f"token={token}",
#     #         {
#     #             "token": token
#     #         }
#     #     )

#     #     for (response, msg) in responses:
#     #         assert response.status_code == 200, msg

#     #         item_collection = self._validate_item_collection(response.json())

#     def test_item_search_limit_param(self):
#         responses = self._fetch(
#             f"limit=100",
#             {
#                 "limit": 100
#             }
#         )

#         for (response, msg) in responses:
#             assert response.status_code == 200, msg

#             item_collection = self._validate_item_collection(response.json())

#             assert len(item_collection.features) <= 100, msg

#     def test_item_search_cql2_filter_param(self):
#         item = self.test_catalog.pick_item()

#         filters = [
#             (
#                 "cql2-json",
#                 {
#                     "op": "a_contains",
#                     "args": [{"property": "keywords"}, ["test"]]
#                 },
#                 lambda feature: "test" in feature["properties"]["keywords"]
#             ),
#             (
#                 "cql2-json",
#                 {
#                     "op": "=",
#                     "args": [{"property": "id"}, item.id]
#                 },
#                 lambda feature: item.id == feature["id"]
#             ),
#             (
#                 "cql2-text",
#                 f"id = '{item.id}'",
#                 lambda feature: item.id == feature["id"]
#             ),
#         ]

#         for (lang, expr, test) in filters:
#             expr_str = json.dumps(expr) if lang == "cql2-json" else expr

#             responses = self._fetch(
#                 f"filter={expr_str}&filter-lang={lang}",
#                 {
#                     "filter": expr,
#                     "filter-lang": lang
#                 }
#             )

#             for (response, msg) in responses:
#                 assert response.status_code == 200, msg

#                 item_collection = self._validate_item_collection(response.json())

#                 for item in item_collection.features:
#                     assert test(item.model_dump()), msg


# class TestItem(BaseTestAPI):

#     def test_item_response_model(self):
#         collection = self.test_catalog.pick_collection()
#         item = self.test_catalog.pick_item(collection=collection)

#         request_href = f"/collections/{collection.id}/items/{item.id}"
#         response = self.client.get(request_href)

#         assert response.status_code == 200, request_href
#         self._validate_item(response.json())


# class TestAllCollections(BaseTestAPI):

#     def test_all_collections_response_model(self):
#         request_href = "/collections"
#         response = self.client.get(request_href)

#         assert response.status_code == 200, request_href
#         TypeAdapter(Collections).validate_json(response.text)

#     @pytest.mark.skip("Not Implemented")
#     def test_all_collections_params(self):
#         ...


# class TestCollection(BaseTestAPI):

#     def test_collection_response_model(self):
#         collection = self.test_catalog.pick_collection()

#         request_href = f"/collections/{collection.id}"
#         response = self.client.get(request_href)

#         assert response.status_code == 200, request_href

#         self._validate_collection(response.json())


# class TestCollectionItems(BaseTestAPI):

#     def test_collection_items_response_model(self):
#         collection = self.test_catalog.pick_collection()

#         request_href = f"/collections/{collection.id}/items"
#         response = self.client.get(request_href)

#         assert response.status_code == 200, request_href

#         self._validate_item_collection(response.json())

#     @pytest.mark.skip("Not Implemented")
#     def test_collection_items_params(self):
#         ...


# class TestQueryable(BaseTestAPI):

#     def test_base_queryables_response_model(self):
#         request_href = "/queryables"
#         response = self.client.get(request_href)

#         assert response.status_code == 200, request_href

#         response_json = response.json()
#         assert response_json["$id"].endswith("/queryables")
#         assert response_json["type"] == "object"
#         assert "properties" in response_json

#     def test_collection_queryables_response_model(self):
#         collection = self.test_catalog.pick_collection()

#         request_href = f"/collections/{collection.id}/queryables"
#         response = self.client.get(request_href)

#         assert response.status_code == 200, request_href

#         response_json = response.json()
#         assert response_json["$id"].endswith("/queryables")
#         assert response_json["type"] == "object"
#         assert "properties" in response_json
