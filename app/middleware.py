from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse

from .crud.vector_tile_assets import (
    get_latest_dynamic_version,
    get_latest_static_version,
)


async def redirect_latest(request: Request, call_next):
    """

    Redirect all GET requests using latest version to actual version number.

    """

    if request.method == "GET" and "latest" in request.url.path:
        path_items = request.url.path.split("/")

        i = 0
        for i, item in enumerate(path_items):
            if item == "latest":
                break
        if i == 0:
            raise HTTPException(status_code=400, detail="Invalid URI")

        if "dynamic" in request.url.path:
            path_items[i] = get_latest_dynamic_version(path_items[i - 1])
        else:
            path_items[i] = get_latest_static_version(path_items[i - 1])
        url = "/".join(path_items)
        return RedirectResponse(url=f"{url}?{request.query_params}")
    else:
        response = await call_next(request)
        return response
