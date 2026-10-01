import httpx
import pendulum
import pytest

from app.utils import planet_quota


@pytest.fixture(autouse=True)
def clear_cache():
    planet_quota.tiles_used_this_month.cache_clear()


def planet(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def report(views: int) -> str:
    return f"date,subscription_id,type,tile_views,email\n2026-10-01,1,basemaps,{views},a@b.c\n"


@pytest.mark.asyncio
async def test_usage_is_only_fetched_once_per_cached_month():
    """The check runs on the tile path, so it must not call Planet every request."""
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, text=report(42))

    async with planet(handler) as client:
        for _ in range(3):
            used = await planet_quota.tiles_used_this_month(
                client,
                subscription_id=1,
                api_key="k",
                month="2026-10",  # pragma: allowlist secret
            )

    assert used == 42
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_a_new_month_is_fetched_again():
    """Keying on the month resets the reading the moment the allowance does."""
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, text=report(42))

    async with planet(handler) as client:
        for month in ("2026-10", "2026-11"):
            await planet_quota.tiles_used_this_month(
                client,
                subscription_id=1,
                api_key="k",
                month=month,  # pragma: allowlist secret
            )

    assert len(calls) == 2


@pytest.mark.asyncio
async def test_planet_being_unreachable_does_not_block_tiles():
    """Unknown usage must serve tiles, and must not retry on every request."""
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(503)

    async with planet(handler) as client:
        for _ in range(3):
            used = await planet_quota.tiles_used_this_month(
                client,
                subscription_id=1,
                api_key="k",
                month="2026-10",  # pragma: allowlist secret
            )

    assert used is None
    assert len(calls) == 1  # the failure is cached too, so an outage can't stampede


def test_the_allowance_returns_at_the_start_of_next_month():
    seconds = planet_quota.seconds_until_quota_reset()

    now = pendulum.now("UTC")
    assert 0 < seconds <= 31 * 24 * 3600
    # Truncated to whole seconds, so it lands just inside the reset boundary.
    assert now.add(seconds=seconds + 1) >= now.start_of("month").add(months=1)
