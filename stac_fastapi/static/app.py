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
logger = logging.getLogger(__name__)

app = make_api(settings).app


def main():
    try:
        import uvicorn

        if settings.reload and settings.environment != "prod":
            settings.reload = False
            logger.warning("Overriding reload setting in non-'prod' environment")

        logger.warning("Settings : %s", settings.model_dump())

        uvicorn.run(
            "stac_fastapi.static.app:app",
            host=settings.app_host,
            port=settings.app_port,
            log_level=settings.log_level,
            reload=settings.reload if not settings.environment == "prod" else False,
            root_path=settings.root_path,
        )
    except ImportError as error:
        raise RuntimeError("Uvicorn must be installed") from error


if __name__ == "__main__":
    main()
