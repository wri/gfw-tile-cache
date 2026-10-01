"""Planet's usage reports, which cover tile streaming for a whole subscription.

This is an account-level API, separate from the WMTS endpoint the tile route
proxies. Reading it needs a Planet key entitled to the subscription; an ordinary key
works, despite what the release doc says about Organization Administrators.
Planet builds the reports daily, each covering the previous 24 hours, so a
report that includes today always undercounts.

The paths and parameters here are what the service actually does, which differs
from Planet's WMTS release doc in three ways, all verified against a real call
on 2026-09-30: the documented `reports/v1` path is a redirect, the id in it is
the subscription id rather than the plan id from the account page, and
`include_user` is required rather than optional.
"""

import csv
import datetime

import httpx

USAGE_REPORT_URL = "https://api.planet.com/receipts/v1/usage-reports/plans/{subscription_id}/tiles/usage/"


def tiles_used(report: str) -> int:
    """Total tile views in a usage report, which Planet returns as CSV.

    One row per user and period, so the total is the sum rather than a single
    figure. Columns: date, subscription_id, type, tile_views, email.
    """
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
