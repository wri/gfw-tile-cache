import httpx
import pendulum
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes import integrated_alerts_planet_imagery as route
from app.settings.globals import GLOBALS

tile_path = "/integrated_alerts_planet_imagery/15/10014/16385.png?month=2020-09"
upstream_url = "https://wmts.example.com"

current_month = pendulum.today().format("YYYY-MM")


def build_client(monkeypatch, handler) -> TestClient:
    """Client for an app with only this route, talking to a stubbed upstream."""
    monkeypatch.setattr(GLOBALS, "planet_integrated_alerts_url", upstream_url)
    monkeypatch.setattr(
        route, "client", httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )
    app = FastAPI()
    app.include_router(route.router)
    return TestClient(app)


def serve_tile(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, content=b"png-bytes")


def refuse_to_serve(request: httpx.Request) -> httpx.Response:
    raise AssertionError("upstream should not be called")


def time_out(request: httpx.Request) -> httpx.Response:
    raise httpx.ReadTimeout("upstream is slow under load")


def test_tile_is_served_from_the_mosaic_for_the_requested_month(monkeypatch):
    requested = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(str(request.url))
        return serve_tile(request)

    response = build_client(monkeypatch, handler).get(tile_path)

    assert response.status_code == 200
    assert response.content == b"png-bytes"
    assert response.headers["content-type"] == "image/png"
    assert response.headers["cache-control"] == "max-age=31536000"
    assert requested == [
        f"{upstream_url}/wmts/v1/planet_medres_visual_2020-09_mosaic/15/10014/16385.png"
    ]


@pytest.mark.parametrize("month", [current_month, "2020-08", "2026-7", "2026-07-15"])
def test_month_outside_the_available_range_is_rejected(monkeypatch, month):
    """Mosaics run from 2020-09 to the last full month, as zero-padded `YYYY-MM`."""
    response = build_client(monkeypatch, refuse_to_serve).get(
        f"/integrated_alerts_planet_imagery/15/10014/16385.png?month={month}"
    )

    assert response.status_code == 422


@pytest.mark.parametrize("zoom", [2, 16])
def test_zoom_outside_the_supported_range_is_rejected(monkeypatch, zoom):
    response = build_client(monkeypatch, refuse_to_serve).get(
        f"/integrated_alerts_planet_imagery/{zoom}/1/1.png?month=2020-09"
    )

    assert response.status_code == 422


def test_unconfigured_upstream_is_reported_as_unavailable(monkeypatch):
    """The URL has no default in code, so a deploy can be missing it."""
    client = build_client(monkeypatch, refuse_to_serve)
    monkeypatch.setattr(GLOBALS, "planet_integrated_alerts_url", None)

    response = client.get(tile_path)

    assert response.status_code == 503


def test_missing_upstream_tile_is_reported_as_not_found(monkeypatch):
    response = build_client(monkeypatch, lambda request: httpx.Response(404)).get(
        tile_path
    )

    assert response.status_code == 404


@pytest.mark.parametrize("handler", [lambda request: httpx.Response(500), time_out])
def test_upstream_failure_is_reported_as_bad_gateway(monkeypatch, handler):
    response = build_client(monkeypatch, handler).get(tile_path)

    assert response.status_code == 502
