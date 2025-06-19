
from starlette.types import ASGIApp, Receive, Scope, Send

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware

from .config import (
    Settings
)


class TimeoutMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            ...

        await self.app(scope, receive, send)


class ProfileMiddleware(BaseHTTPMiddleware):

    _settings: Settings

    def __init__(self, app, settings: Settings):
        super().__init__(app)

        self._settings = settings

    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # if self._settings.profile:
        #     response.headers["X-SETTING-assume_best_practice_layout"] = str(self._settings.assume_best_practice_layout)
        #     response.headers["X-SETTING-cache"] = str(self._settings.cache)

        return response
