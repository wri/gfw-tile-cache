import os

# from app.main import LOGGER
from fastapi import APIRouter
from starlette.responses import HTMLResponse


router = APIRouter()


@router.get("/")
async def root():
    # LOGGER.info("Root request")
    return {"message": "Hello World"}


@router.get("/nasa_viirs_fire_alerts/latest/mapbox.html", response_class=HTMLResponse)
async def mapbox():
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, "static/mapbox.html"), "r") as myfile:
        html_content = myfile.read()
    return HTMLResponse(content=html_content, status_code=200)


@router.get("/nasa_viirs_fire_alerts/latest/esri.html", response_class=HTMLResponse)
async def esri():
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, "static/esri.html"), "r") as myfile:
        html_content = myfile.read()
    return HTMLResponse(content=html_content, status_code=200)
