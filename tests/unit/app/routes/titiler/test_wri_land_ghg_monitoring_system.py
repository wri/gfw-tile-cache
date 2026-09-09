import numpy as np
import pytest
from cogeo_mosaic.errors import NoAssetFoundError
from fastapi import FastAPI
from fastapi.testclient import TestClient
from rasterio.errors import RasterioIOError
from rio_tiler.errors import EmptyMosaicError, TileOutsideBounds
from rio_tiler.models import ImageData

from app.routes.titiler import wri_land_ghg_monitoring_system as route

tile_path = "/wri_land_ghg_monitoring_system/v1.0.3/dynamic/3/2/4.png"


def build_client(monkeypatch, read_asset) -> TestClient:
    """Client for an app with only this route, reading stubbed rasters."""
    monkeypatch.setattr(route, "read_asset", read_asset)
    app = FastAPI()
    app.include_router(route.router)
    return TestClient(app)


def serve_raster(asset, tile_x, tile_y, zoom, value=1.0) -> ImageData:
    return ImageData(
        np.ma.MaskedArray(np.full((1, 4, 4), value, dtype="float32"), mask=False)
    )


def refuse_to_read(asset, tile_x, tile_y, zoom) -> ImageData:
    raise AssertionError("no raster should be read")


@pytest.mark.parametrize(
    "layer, flux_type, expected_files",
    [
        ("lulucf", "net", ["mosaic.json"]),
        (
            "agriculture",
            "gross_emissions",
            ["cropland_emissions_per_ha.tif", "livestock_emissions_per_ha.tif"],
        ),
    ],
)
def test_tile_is_rendered_from_the_layers_rasters(
    monkeypatch, layer, flux_type, expected_files
):
    read = []

    def read_asset(asset, tile_x, tile_y, zoom) -> ImageData:
        read.append(asset.file_name)
        return serve_raster(asset, tile_x, tile_y, zoom)

    response = build_client(monkeypatch, read_asset).get(
        f"{tile_path}?layer={layer}&flux_type={flux_type}"
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert read == expected_files


def test_flux_type_the_layer_has_no_raster_for_is_rejected(monkeypatch):
    response = build_client(monkeypatch, refuse_to_read).get(
        f"{tile_path}?layer=agriculture&flux_type=net"
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "error", [TileOutsideBounds, NoAssetFoundError, EmptyMosaicError]
)
def test_tile_without_data_is_not_found(monkeypatch, error):
    def read_asset(asset, tile_x, tile_y, zoom) -> ImageData:
        raise error("nothing here")

    response = build_client(monkeypatch, read_asset).get(
        f"{tile_path}?layer=lulucf&flux_type=net"
    )

    assert response.status_code == 404


def test_agriculture_layers_use_their_own_colour_ramp(monkeypatch):
    """0.5 Mg/ha is mid-ramp for agriculture but near-zero for LULUCF."""

    def read_asset(asset, tile_x, tile_y, zoom) -> ImageData:
        return serve_raster(asset, tile_x, tile_y, zoom, value=0.5)

    client = build_client(monkeypatch, read_asset)
    agriculture = client.get(f"{tile_path}?layer=cropland&flux_type=gross_emissions")
    lulucf = client.get(f"{tile_path}?layer=lulucf&flux_type=net")

    assert agriculture.status_code == lulucf.status_code == 200
    assert agriculture.content != lulucf.content


def test_unreadable_raster_is_reported_as_unavailable(monkeypatch):
    """A renamed or unreadable raster is an outage, not a missing tile."""

    def read_asset(asset, tile_x, tile_y, zoom) -> ImageData:
        raise RasterioIOError("cannot read")

    response = build_client(monkeypatch, read_asset).get(
        f"{tile_path}?layer=lulucf&flux_type=net"
    )

    assert response.status_code == 503
