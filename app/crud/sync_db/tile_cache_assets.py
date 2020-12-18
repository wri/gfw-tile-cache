from typing import Any, Dict, List, Optional, Tuple

from cachetools import TTLCache, cached
from fastapi.logger import logger

from ...application import get_synchronous_db


# @cached(cache=TTLCache(maxsize=15, ttl=900))
def get_datasets(asset_type: str) -> List[str]:
    with get_synchronous_db() as db:
        rows = db.execute(
            """SELECT DISTINCT
                    dataset
                   FROM assets
                   WHERE asset_type = :asset_type
                    AND status = 'saved'""",
            {"asset_type": asset_type},
        ).fetchall()

    datasets = [row[0] for row in rows]

    return datasets


# @cached(cache=TTLCache(maxsize=15, ttl=900))
def get_versions(dataset: str, asset_type: str) -> List[Tuple[str, str]]:
    with get_synchronous_db() as db:
        rows = db.execute(
            """SELECT DISTINCT
                    version
                   FROM assets
                   WHERE asset_type = :asset_type
                    AND status = 'saved'
                    AND dataset = :dataset""",
            {"dataset": dataset, "asset_type": asset_type},
        ).fetchall()

    versions = [row[0] for row in rows]

    return versions


# @cached(cache=TTLCache(maxsize=15, ttl=900))
def get_latest_version(dataset: str, asset_type: str) -> Optional[str]:
    with get_synchronous_db() as db:
        row = db.execute(
            """SELECT DISTINCT
                    versions.version
                   FROM versions
                    JOIN assets
                    ON versions.dataset = assets.dataset
                        AND versions.version = assets.version
                   WHERE assets.asset_type = :asset_type
                    AND assets.status = 'saved'
                    AND versions.is_latest = true
                    AND versions.dataset = :dataset""",
            {"dataset": dataset, "asset_type": asset_type},
        ).fetchone()

    if not row or not row[0]:
        logger.warning(f"Did not found `latest` version for {asset_type} of {dataset}.")
        latest = None
    else:
        latest = row[0]

    return latest


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
        latest_versions = rows

    return [{"dataset": row[0], "version": row[1]} for row in latest_versions]


# @cached(cache=TTLCache(maxsize=15, ttl=900))
def get_attributes(dataset: str, version: str, asset_type: str) -> List[Dict[str, Any]]:
    with get_synchronous_db() as db:
        row = db.execute(
            """SELECT DISTINCT
                    fields
                   FROM assets
                   WHERE asset_type = :asset_type
                    AND status = 'saved'
                    AND dataset = :dataset
                    AND version = :version""",
            {"dataset": dataset, "version": version, "asset_type": asset_type},
        ).fetchone()

    if not row or not row[0]:
        attributes = []
        logger.warning(
            f"Did not find any fields in metadata for {asset_type} of {dataset}.{version}."
        )
    else:
        attributes = row[0]
    return attributes
