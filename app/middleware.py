from fastapi import Request, Response


async def no_cache_response_header(request: Request, call_next):
    """This middleware adds a no-cache response header to documentation endpoints."""

    no_cache_endpoints = ["/", "/openapi.json", "docs"]
    response: Response = await call_next(request)

    if request.method == "GET" and request.url.path in no_cache_endpoints:
        response.headers["Cache-Control"] = "no-cache"

    return response
