import httpx
import pendulum
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes import integrated_alerts_planet_imagery as route
from app.settings.globals import GLOBALS

tile_path = "/integrated_alerts_planet_imagery/15/10014/16385.png?month=2020-09"
upstream_url = "https://wmts.example.com"


def month(months_ago: int) -> str:
    """`YYYY-MM` relative to the current month; negative reaches into the future."""
    return pendulum.today().subtract(months=months_ago).format("YYYY-MM")


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


def test_tile_is_served_from_the_mosaic_for_the_requested_month(monkeypatch):
    requested = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(str(request.url))
        return serve_tile(request)

    response = build_client(monkeypatch, handler).get(tile_path)

    assert response.status_code == 200
    assert response.content == b"png-bytes"
    assert response.headers["content-type"] == "image/png"
    assert requested == [
        f"{upstream_url}/wmts/v1/planet_medres_visual_2020-09_mosaic/15/10014/16385.png"
    ]


@pytest.mark.parametrize("months_ahead", [0, 1])
def test_month_after_the_last_full_calendar_month_is_rejected(
    monkeypatch, months_ahead
):
    """The current month's mosaic is still being built, and later ones don't exist."""
    response = build_client(monkeypatch, refuse_to_serve).get(
        f"/integrated_alerts_planet_imagery/15/10014/16385.png?month={month(-months_ahead)}"
    )

    assert response.status_code == 422


@pytest.mark.parametrize("month_before_archive", ["2020-08", "2019-01"])
def test_month_before_the_archive_start_is_rejected(monkeypatch, month_before_archive):
    """The Planet archive begins at 2020-09; nothing exists before it."""
    response = build_client(monkeypatch, refuse_to_serve).get(
        f"/integrated_alerts_planet_imagery/15/10014/16385.png?month={month_before_archive}"
    )

    assert response.status_code == 422


def test_imagery_is_cached_for_a_year(monkeypatch):
    """Every month that gets served is complete, so nothing needs revisiting."""
    response = build_client(monkeypatch, serve_tile).get(
        f"/integrated_alerts_planet_imagery/15/10014/16385.png?month={month(1)}"
    )

    assert response.headers["cache-control"] == "max-age=31536000"


def test_month_is_required(monkeypatch):
    response = build_client(monkeypatch, refuse_to_serve).get(
        "/integrated_alerts_planet_imagery/15/10014/16385.png"
    )

    assert response.status_code == 422


@pytest.mark.parametrize("month", ["2026-7", "2026-13", "2026-07-15", "july-2026"])
def test_month_must_be_a_zero_padded_year_month(monkeypatch, month):
    response = build_client(monkeypatch, refuse_to_serve).get(
        f"/integrated_alerts_planet_imagery/15/10014/16385.png?month={month}"
    )

    assert response.status_code == 422


@pytest.mark.parametrize("zoom", [2, 16])
def test_zoom_outside_the_supported_range_is_rejected(monkeypatch, zoom):
    response = build_client(monkeypatch, refuse_to_serve).get(
        f"/integrated_alerts_planet_imagery/{zoom}/1/1.png?month=2026-07"
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


def test_failing_upstream_is_reported_as_bad_gateway(monkeypatch):
    response = build_client(monkeypatch, lambda request: httpx.Response(500)).get(
        tile_path
    )

    assert response.status_code == 502


def test_unreachable_upstream_is_reported_as_bad_gateway(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("upstream is slow under load")

    response = build_client(monkeypatch, handler).get(tile_path)

    assert response.status_code == 502
