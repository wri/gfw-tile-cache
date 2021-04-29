from fastapi import Request, Response


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
