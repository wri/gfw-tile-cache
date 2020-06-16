from typing import List

from cachetools import TTLCache, cached
from fastapi import HTTPException

from app.application import get_synchronous_db
from app.models.pydantic.versions import LatestVersion


@cached(cache=TTLCache(maxsize=1, ttl=900))
def get_latest_versions() -> List[LatestVersion]:
    with get_synchronous_db() as db:
        rows = db.execute(
            """SELECT DISTINCT
                versions.dataset,
                versions.version
               FROM versions
               WHERE versions.status = 'saved'
                AND versions.is_latest = true"""
        )

    latest_versions = rows.fetchall()
    if not latest_versions:
        raise HTTPException(
            status_code=400,
            detail="There are no latest versions registered with the API.",
        )

    return [LatestVersion(dataset=row[0], version=row[1]) for row in latest_versions]
