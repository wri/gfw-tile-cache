from pathlib import Path

import httpx
import pendulum
import pytest

from app.utils.planet_usage import fetch_monthly_usage, tiles_used

report = (
    Path(__file__).parents[3] / "fixtures" / "planet_usage_report.csv"
).read_text()


def test_every_row_of_the_report_counts_towards_the_total():
    """Planet returns CSV with a row per user and period, not a single figure."""
    assert tiles_used(report) == 6802


@pytest.mark.asyncio
async def test_usage_is_requested_for_the_current_month_to_date():
    """Planet bills per calendar month, so the window starts on the 1st."""
    requested = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(request)
        return httpx.Response(200, text=report)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        used = await fetch_monthly_usage(
            client,
            subscription_id=800877,
            api_key="planet-key",  # pragma: allowlist secret
            today=pendulum.date(2026, 9, 30),
        )

    assert used == 6802
    url = requested[0].url
    assert url.path == "/receipts/v1/usage-reports/plans/800877/tiles/usage/"
    assert dict(url.params) == {
        "start": "2026-09-01",
        "end": "2026-09-30",
        "interval": "monthly",
        "type": "basemaps",
        "include_user": "true",  # required: omitting it is a 400
    }


@pytest.mark.asyncio
async def test_an_error_from_planet_is_raised():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(403))
    ) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await fetch_monthly_usage(
                client,
                subscription_id=800877,
                api_key="planet-key",  # pragma: allowlist secret
                today=pendulum.date(2026, 9, 30),
            )
