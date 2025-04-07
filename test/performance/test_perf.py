import time
import shapely

import pytest

from test.conftest import (
    rfc3339,
    BaseTestAPI,
)

from test.performance.conftest import (
    Perfs
)

from stac_fastapi.static.core import WalkPath

execution_number = 1


@pytest.mark.skip("Obsolete")
@pytest.mark.perf
class TestAPIPerfs(BaseTestAPI):

    def time_get(self, url: str):
        start = time.time()
        response = self.client.get(url)
        end = time.time()

        assert response.status_code == 200

        return (end - start) * 1000

    @pytest.mark.parametrize("execution_number", range(execution_number))
    def test_item_search_collections_param(self, perfs: Perfs, execution_number):
        collection = self.test_catalog.pick_collection()

        perfs.collect(
            "/search?[collections=]",
            self.time_get(f"/search?collections={collection.id}")
        )

    @pytest.mark.parametrize("execution_number", range(execution_number))
    def test_item_search_ids_param(self, perfs: Perfs, execution_number):
        item = self.test_catalog.pick_item()

        perfs.collect(
            "/search?[ids=]",
            self.time_get(f"/search?ids={item.id}")
        )

    @pytest.mark.parametrize("execution_number", range(execution_number))
    def test_item_search_bbox_param(self, perfs: Perfs, execution_number):
        bbox = self.test_catalog.pick_bbox()
        bbox = ",".join([
            str(coordinate)
            for coordinate in bbox
        ])

        perfs.collect(
            "/search?[bbox=]",
            self.time_get(f"/search?bbox={bbox}")
        )

    @pytest.mark.parametrize("execution_number", range(execution_number))
    def test_item_search_intersects_param(self, perfs: Perfs, execution_number):
        geometry = self.test_catalog.pick_geometry()
        geometry = shapely.to_wkt(geometry)

        perfs.collect(
            "/search?[intersects=]",
            self.time_get(f"/search?intersects={geometry}")
        )

    @pytest.mark.parametrize("execution_number", range(execution_number))
    def test_item_search_datetime_param(self, perfs: Perfs, execution_number):
        datetime_interval = self.test_catalog.pick_datetime_interval()

        datetime_str = rfc3339.datetime_to_str(datetime_interval)

        datetime_param = f"datetime={datetime_str}" if datetime_str else ""

        perfs.collect(
            "/search?[datetime=]",
            self.time_get(f"/search?" + datetime_param)
        )

    @pytest.mark.parametrize("execution_number", range(execution_number))
    def test_item_search_token_param(self, perfs: Perfs, execution_number):
        bookmark = WalkPath.encode(*[
            stac_object.get_self_href()
            for stac_object
            in self.test_catalog.pick_walk()
        ])
        token = f"next:{str(bookmark)}"

        perfs.collect(
            "/search?[token=]",
            self.time_get(f"/search?token={token}")
        )

    @pytest.mark.parametrize("execution_number", range(execution_number))
    def test_item_search_cql2_filter_param(self, perfs: Perfs, execution_number):
        item = self.test_catalog.pick_item()

        perfs.collect(
            "/search?[filter=]",
            self.time_get(f"/search?filter=id='{item.id}'")
        )
