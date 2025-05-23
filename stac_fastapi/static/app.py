import logging
import os
from pprint import pprint as print

from pydantic import ValidationError

from stac_fastapi.static.api import (
    Settings,
    make_api
)

try:
    settings = Settings()
except ValidationError as error:
    logging.critical(error)
    exit(2)

logging.basicConfig(
    level=settings.log_level.upper()
)

app = make_api(settings).app


def main():
    try:
        import uvicorn

        print(settings.model_dump())

        uvicorn.run(
            "stac_fastapi.static.app:app",
            host=settings.app_host,
            port=settings.app_port,
            log_level=settings.log_level,
            reload=settings.reload,
            root_path=settings.root_path,
        )
    except ImportError as e:
        raise RuntimeError(
            "Uvicorn must be installed in order to use command") from e


if __name__ == "__main__":
    main()
