import json
import os

# from app.main import LOGGER
from fastapi import APIRouter


router = APIRouter()


@router.get("/nasa_viirs_fire_alerts/latest/root.json")
async def root_json():
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, "static/root.json"), "r") as myfile:
        json_content = json.loads(myfile.read())
    return json_content


@router.get("/nasa_viirs_fire_alerts/latest/default/VectorTileServer")
async def vector_tile_server():
    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, "static/VectorTileServer.json"), "r") as myfile:
        json_content = json.loads(myfile.read())
    return json_content
