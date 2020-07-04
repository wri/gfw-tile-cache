from typing import Dict, List

from cachetools import TTLCache, cached
from fastapi.logger import logger

from ...application import get_synchronous_db


@cached(cache=TTLCache(maxsize=1, ttl=900))
def get_latest_versions() -> List[Dict[str, str]]:
    with get_synchronous_db() as db:
        rows = db.execute(
            """SELECT DISTINCT
                versions.dataset,
                versions.version
               FROM versions
               WHERE versions.status = 'saved'
                AND versions.is_latest = true"""
        ).fetchall()

    if not rows:
        latest_versions = []
        logger.warning("There are no latest versions registered with the API.")
    else:
        latest_versions = rows.fetchall()

    return [{"dataset": row[0], "version": row[1]} for row in latest_versions]
