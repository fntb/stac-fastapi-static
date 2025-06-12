from multiprocessing import Process

import pytest

from stac_fastapi.static.app import (
    main,
    settings
)


def pytest_addoption(parser):
    parser.addoption("--target", action="store", default=None)


@pytest.fixture(scope="session")
def api_base_href(pytestconfig):
    if (target := pytestconfig.getoption('target')):
        yield target
    else:
        proc = Process(target=main, args=(), daemon=True)
        proc.start()

        yield f"http://{settings.app_host}:{str(settings.app_port)}/{settings.root_path}"

        proc.kill()
