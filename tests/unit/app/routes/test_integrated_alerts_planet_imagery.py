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
    assert response.headers["cache-control"].startswith("max-age=")
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


@pytest.mark.parametrize("zoom", [9, 16])
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


async def exhausted():
    return True


async def not_exhausted():
    return False


def test_exhausted_quota_is_rejected_without_calling_planet(monkeypatch):
    monkeypatch.setattr(route, "quota_exhausted", exhausted)

    response = build_client(monkeypatch, refuse_to_serve).get(tile_path)

    assert response.status_code == 429
    assert int(response.headers["retry-after"]) > 0
    assert response.headers["cache-control"] == "no-store"


def test_a_tile_is_still_served_while_the_quota_lasts(monkeypatch):
    monkeypatch.setattr(route, "quota_exhausted", not_exhausted)

    response = build_client(monkeypatch, serve_tile).get(tile_path)

    assert response.status_code == 200


@pytest.mark.parametrize(
    "now, expires",
    [
        ("2026-10-01T00:00:00Z", "2026-10-16T00:00:00Z"),  # before this month's refresh
        ("2026-10-15T23:59:59Z", "2026-10-16T00:00:00Z"),  # the night the refresh lands
        (
            "2026-10-16T00:00:00Z",
            "2026-11-16T00:00:00Z",
        ),  # on the boundary, wait for next
        ("2026-10-20T12:00:00Z", "2026-11-16T00:00:00Z"),  # after it, next month
        ("2026-12-20T12:00:00Z", "2027-01-16T00:00:00Z"),  # across the year
    ],
)
def test_tiles_expire_when_planet_republishes_the_alert_mask(now, expires):
    seconds = route.seconds_until_alert_refresh(pendulum.parse(now))

    assert pendulum.parse(now).add(seconds=seconds) == pendulum.parse(expires)


def test_the_tile_is_cached_until_the_refresh(monkeypatch):
    monkeypatch.setattr(route, "quota_exhausted", not_exhausted)

    response = build_client(monkeypatch, serve_tile).get(tile_path)

    age = int(response.headers["cache-control"].split("max-age=")[1])
    assert 0 < age <= 31 * 24 * 3600


@pytest.fixture(autouse=True)
def clear_usage_cache():
    route.tiles_used_this_month.cache_clear()


def usage_report(views: int) -> str:
    return f"date,subscription_id,type,tile_views,email\n2026-10-01,1,basemaps,{views},a@b.c\n"


def stub_planet(monkeypatch, handler):
    monkeypatch.setattr(
        route, "client", httpx.AsyncClient(transport=httpx.MockTransport(handler))
    )


def test_every_row_of_the_report_counts_towards_the_total():
    rows = usage_report(42) + "2026-10-01,1,basemaps,8,a@b.c\n"

    assert route.tiles_used(rows) == 50


@pytest.mark.asyncio
async def test_usage_is_requested_for_the_current_month_to_date(monkeypatch):
    requested = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(request)
        return httpx.Response(200, text=usage_report(6802))

    stub_planet(monkeypatch, handler)
    used = await route.fetch_monthly_usage(
        800877, "planet-key", pendulum.date(2026, 9, 30)  # pragma: allowlist secret
    )

    assert used == 6802
    assert (
        requested[0].url.path == "/receipts/v1/usage-reports/plans/800877/tiles/usage/"
    )
    assert dict(requested[0].url.params) == {
        "start": "2026-09-01",
        "end": "2026-09-30",
        "interval": "monthly",
        "type": "basemaps",
        "include_user": "true",
    }


@pytest.mark.asyncio
async def test_the_usage_request_gives_up_quickly(monkeypatch):
    requested = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(request)
        return httpx.Response(200, text=usage_report(1))

    stub_planet(monkeypatch, handler)
    await route.fetch_monthly_usage(1, "k", pendulum.date(2026, 10, 1))

    assert requested[0].extensions["timeout"]["read"] == route.USAGE_TIMEOUT_SECONDS


@pytest.mark.asyncio
async def test_an_error_from_planet_is_raised(monkeypatch):
    stub_planet(monkeypatch, lambda request: httpx.Response(403))

    with pytest.raises(httpx.HTTPStatusError):
        await route.fetch_monthly_usage(
            800877, "planet-key", pendulum.date(2026, 9, 30)  # pragma: allowlist secret
        )


@pytest.mark.asyncio
async def test_usage_is_only_fetched_once_per_cached_month(monkeypatch):
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, text=usage_report(42))

    stub_planet(monkeypatch, handler)
    for _ in range(3):
        used = await route.tiles_used_this_month(1, "k", "2026-10")

    assert used == 42
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_a_new_month_is_fetched_again(monkeypatch):
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, text=usage_report(42))

    stub_planet(monkeypatch, handler)
    for month in ("2026-10", "2026-11"):
        await route.tiles_used_this_month(1, "k", month)

    assert len(calls) == 2


@pytest.mark.asyncio
async def test_planet_being_unreachable_does_not_block_tiles(monkeypatch):
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(503)

    stub_planet(monkeypatch, handler)
    for _ in range(3):
        used = await route.tiles_used_this_month(1, "k", "2026-10")

    assert used is None
    assert len(calls) == 1


def test_the_allowance_returns_at_the_start_of_next_month():
    now = pendulum.now("UTC")
    seconds = route.seconds_until_quota_reset()

    assert 0 < seconds <= 31 * 24 * 3600
    assert now.add(seconds=seconds + 1) >= now.start_of("month").add(months=1)
