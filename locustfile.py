
import locust
import shapely
import random

from test.conftest import (
    TestCatalog,
    rfc3339,
    test_catalog as make_test_catalog
)

from stac_fastapi.static.core import WalkPath


test_catalog = make_test_catalog()


class TestSearch(locust.HttpUser):

    @locust.task(1)
    def search(self):
        self.client.get("/search", name="/search")

    @locust.task(1)
    def search_page(self):
        bookmark = WalkPath.encode(*[
            stac_object.get_self_href()
            for stac_object
            in test_catalog.pick_walk()
        ])

        if random.randint(0, 1):
            token = f"next:{str(bookmark)}"
        else:
            token = f"prev:{str(bookmark)}"

        self.client.get(f"/search?" + token, name="/search?token=[token]")

    @locust.task(1)
    @locust.tag("debug")
    def search_item_by_id(self):
        item = test_catalog.pick_item()

        self.client.get(f"/search?ids={item.id}", name="/search?ids=[ids]")

    @locust.task(1)
    def search_by_collection_id(self):
        collection = test_catalog.pick_collection()

        self.client.get(
            f"/search?collections={collection.id}", name="/search?collections=[collections]")

    @locust.task(1)
    def search_items_by_bbox(self):
        bbox = test_catalog.pick_bbox()
        bbox = ",".join([
            str(coordinate)
            for coordinate in bbox
        ])

        self.client.get(f"/search?bbox={bbox}", name="/search?bbox=[bbox]")

    @locust.task(1)
    def search_items_by_geometry(self):
        geometry = test_catalog.pick_geometry()
        geometry = shapely.to_geojson(geometry)

        self.client.get(
            f"/search?intersects={geometry}", name="/search?intersects=[geometry]")

    @locust.task(1)
    def search_items_by_datetime(self):
        datetime_interval = test_catalog.pick_datetime_interval()

        datetime_str = rfc3339.datetime_to_str(datetime_interval)

        datetime_param = f"datetime={datetime_str}" if datetime_str else ""

        self.client.get(f"/search?" + datetime_param,
                        name="/search?datetime=[datetime]")

    # @locust.task(1)
    # def search_items_by_filter(self):
    #     item = test_catalog.pick_item()

    #     self.client.get(f"/search?filter=id='" + item.id + "'",
    #                     name="/search?filter=[filter]")
