from typing import Iterator
import uuid
import random

import pytest

from stac_pydantic.item import Item

from stac_fastapi.static.core import (
    WalkResult,
    WalkPath,
    WalkMarker,
    WalkPage
)

from stac_fastapi.static.core.requests import FileSession
from stac_fastapi.static.api import Settings


@pytest.fixture
def walk() -> list[WalkResult]:
    walk: list[WalkResult] = []

    for i in range(100):
        href = str(i)
        walk_path = WalkPath.encode_part(href)

        walk.append(WalkResult(
            href=href,
            walk_path=walk_path,
            type=Item,
            _session=FileSession(),
            _settings=Settings(
                catalog_href="file:///dev/null"
            )
        ))

    walk.sort(
        key=lambda walk_result: walk_result.walk_path
    )

    return walk


class TestPagination():

    def test_first_page(self, walk: list[WalkResult]):
        page_len = 10

        first_page = WalkPage.paginate(
            walk,
            None,
            page_len
        )

        assert first_page.page == walk[:page_len]
        assert first_page.prev == None
        assert first_page.next == walk[page_len - 1].walk_path

        first_page = WalkPage.paginate(
            walk,
            WalkMarker(
                walk[page_len - 1].walk_path,
                direction="prev"
            ),
            page_len
        )

        assert first_page.page == walk[:page_len]
        assert first_page.prev == None
        assert first_page.next == walk[page_len - 1].walk_path

    def test_last_page(self, walk: list[WalkResult]):
        page_len = 1

        last_page = WalkPage.paginate(
            walk,
            WalkMarker(
                walk[-(page_len+1)].walk_path,
                direction="next"
            ),
            page_len
        )

        assert last_page.page == walk[-page_len:]
        assert last_page.prev == walk[-(page_len + 1)].walk_path
        assert last_page.next == None

    def test_next_and_prev_pages(self, walk: list[WalkResult]):
        page_len = 10

        page = WalkPage.paginate(
            walk,
            WalkMarker(
                walk[50].walk_path,
                direction="next"
            ),
            page_len
        )

        assert page.page == walk[50 + 1:(50 + page_len + 1)]
        assert page.next == walk[50 + page_len].walk_path
        assert page.prev == walk[50].walk_path

        page = WalkPage.paginate(
            walk,
            WalkMarker(
                page.prev,
                direction="prev"
            ),
            page_len
        )

        assert page.page == walk[50 + 1 - page_len:50 + 1]
        assert page.next == walk[50].walk_path
        assert page.prev == walk[50 - page_len].walk_path

        page = WalkPage.paginate(
            walk,
            WalkMarker(
                page.next,
                direction="next"
            ),
            page_len
        )

        assert page.page == walk[50 + 1:(50 + page_len + 1)]
        assert page.next == walk[50 + page_len].walk_path
        assert page.prev == walk[50].walk_path
