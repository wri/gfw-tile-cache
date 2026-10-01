"""Planet tile streaming usage for a subscription.

Reports are built daily and cover the previous 24 hours, so one including today
undercounts.
"""

import csv
import datetime

import httpx

USAGE_REPORT_URL = "https://api.planet.com/receipts/v1/usage-reports/plans/{subscription_id}/tiles/usage/"


def tiles_used(report: str) -> int:
    """Total tile views in a usage report, which Planet returns as CSV."""
    return sum(int(row["tile_views"]) for row in csv.DictReader(report.splitlines()))


async def fetch_monthly_usage(
    client: httpx.AsyncClient,
    *,
    subscription_id: int,
    api_key: str,
    today: datetime.date,
) -> int:
    """Tile views billed to the subscription since the start of `today`'s month."""
    response = await client.get(
        USAGE_REPORT_URL.format(subscription_id=subscription_id),
        auth=(api_key, ""),
        params={
            "start": today.replace(day=1).isoformat(),
            "end": today.isoformat(),
            "interval": "monthly",
            "type": "basemaps",
            "include_user": "true",
        },
    )
    response.raise_for_status()
    return tiles_used(response.text)
