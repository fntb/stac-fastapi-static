
import pytest
import pystac

from stac_fastapi.static.app import settings

from stac_fastapi.static.core.requests import (
    FileSession,
    Session,
    is_file_uri,
)


@pytest.fixture(scope="session")
def catalog_href():
    return settings.catalog_href


@pytest.fixture(scope="session")
def session(catalog_href: str):
    if is_file_uri(catalog_href):
        return FileSession()
    else:
        return Session()


@pytest.fixture(scope="session")
def catalog(catalog_href: str):
    def _make_catalog(catalog_href: str):
        for cls in (pystac.Catalog, pystac.Collection):
            try:
                return cls.from_file(catalog_href)
            except Exception:
                pass

        raise ValueError("Not a Catalog or Collection")

    return _make_catalog(catalog_href)
