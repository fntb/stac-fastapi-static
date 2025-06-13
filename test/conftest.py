from multiprocessing import Process
import time

import pytest
import pystac

from stac_fastapi.static.app import (
    main,
    settings
)

from stac_fastapi.static.core.requests import (
    FileSession,
    Session,
    is_file_uri,
)


def pytest_addoption(parser):
    parser.addoption("--api-base-href", action="store", default="default")


@pytest.fixture(scope="session")
def api_base_href(pytestconfig):
    if (api_base_href := pytestconfig.getoption("api_base_href")) != "default":
        yield api_base_href
    else:
        proc = Process(target=main, args=(), daemon=True)
        proc.start()
        time.sleep(1)

        assert proc.is_alive(), proc.exitcode

        yield f"http://{settings.app_host}:{str(settings.app_port)}/{settings.root_path}"

        proc.kill()


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
