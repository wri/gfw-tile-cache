import re
from typing import Sequence

from fastapi import Request, Response
from starlette.datastructures import Headers
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send


class TileCacheCORSMiddleware(CORSMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        allow_origins: Sequence[str] = (),
        allow_methods: Sequence[str] = ("GET",),
        allow_headers: Sequence[str] = (),
        allow_credentials: bool = False,
        allow_origin_regex: str = None,
        expose_headers: Sequence[str] = (),
        max_age: int = 600,
        exclude_routes: Sequence[str] = (),
        include_routes: Sequence[str] = (),
    ) -> None:
        super().__init__(
            app,
            allow_origins,
            allow_methods,
            allow_headers,
            allow_credentials,
            allow_origin_regex,
            expose_headers,
            max_age,
        )
        self.exclude_routes = exclude_routes
        self.include_routes = include_routes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":  # pragma: no cover
            await self.app(scope, receive, send)
            return

        method = scope["method"]
        headers = Headers(scope=scope)
        origin = headers.get("origin")
        request = Request(scope, receive)

        exclude_regex = "(?:% s)" % "|".join(self.exclude_routes)
        include_regex = "(?:% s)" % "|".join(self.include_routes)

        if origin is None or (
            self.exclude_routes and re.match(exclude_regex, request.url.path)
        ):
            return await self._fallback(scope, receive, send)

        elif not self.include_routes or (
            self.include_routes and re.match(include_regex, request.url.path)
        ):
            if method == "OPTIONS" and "access-control-request-method" in headers:
                return await self._option(scope, receive, send, headers)
            await self.simple_response(scope, receive, send, request_headers=headers)

        else:
            return await self._fallback(scope, receive, send)

    async def _fallback(self, scope, receive, send) -> None:
        await self.app(scope, receive, send)

    async def _option(self, scope, receive, send, headers) -> None:
        response = self.preflight_response(request_headers=headers)
        await response(scope, receive, send)


async def no_cache_response_header(request: Request, call_next):
    """This middleware adds a cache control response header.

    Documentation related responses are not cached at all.
    Otherwise, cache time is set to 1 year unless already specified differently in the response.
    """

    no_cache_endpoints = ["/", "/openapi.json", "docs"]
    response: Response = await call_next(request)

    if request.method == "GET" and request.url.path in no_cache_endpoints:
        response.headers["Cache-Control"] = "no-cache"
    elif request.method == "GET" and response.status_code < 300:
        max_age = response.headers.get("Cache-Control", "max-age=31536000")
        response.headers["Cache-Control"] = max_age

    return response
