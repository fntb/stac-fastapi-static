import logging
import os

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
    level=settings.log_level
)

app = make_api(settings).app


def run():
    """Run app from command line using uvicorn if available."""
    try:
        import uvicorn

        uvicorn.run(
            "stac_fastapi.static.app:app",
            host=settings.app_host,
            port=settings.app_port,
            log_level=settings.log_level,
            reload=settings.reload,
            root_path=os.getenv("UVICORN_ROOT_PATH", ""),
        )
    except ImportError as e:
        raise RuntimeError(
            "Uvicorn must be installed in order to use command") from e


if __name__ == "__main__":
    run()
