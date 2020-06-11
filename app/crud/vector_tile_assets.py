from typing import Any, Dict, List, Tuple

from cachetools import TTLCache, cached
from fastapi import HTTPException
from sqlalchemy.sql import text

from app.application import get_synchronous_db

static_asset = "Static vector tile cache"
dynamic_asset = "Dynamic vector tile cache"


def dataset_constructor(asset_type):
    @cached(cache=TTLCache(maxsize=15, ttl=900))
    def get_datasets() -> List[str]:
        with get_synchronous_db() as db:
            rows = db.execute(
                """SELECT DISTINCT
                    dataset
                   FROM assets
                   WHERE asset_type = :asset_type
                    AND status = 'saved'""",
                {"asset_type": asset_type},
            )

        return [row.dataset for row in rows]

    return get_datasets


get_static_datasets = dataset_constructor(static_asset)
get_dynamic_datasets = dataset_constructor(dynamic_asset)


def version_constructor(asset_type):
    # memorize fields for 15 min
    @cached(cache=TTLCache(maxsize=15, ttl=900))
    def get_versions(dataset) -> List[Tuple[str, str]]:
        with get_synchronous_db() as db:
            rows = db.execute(
                """SELECT DISTINCT
                    version
                   FROM assets
                   WHERE asset_type = :asset_type
                    AND status = 'saved'
                    AND dataset = :dataset""",
                {"dataset": dataset, "asset_type": asset_type},
            )

        if not rows:
            raise HTTPException(
                status_code=400, detail=f"Dataset {dataset} has no dynamic tile cache.",
            )

        return [row.version for row in rows]

    return get_versions


get_static_versions = version_constructor(static_asset)
get_dynamic_versions = version_constructor(dynamic_asset)


def latest_version_constructor(asset_type):
    # memorize fields for 15 min
    @cached(cache=TTLCache(maxsize=15, ttl=900))
    def get_latest_version(dataset: str) -> str:
        with get_synchronous_db() as db:
            latest = db.scalar(
                """SELECT DISTINCT
                    versions.version
                   FROM versions
                    JOIN assets
                    ON versions.dataset = assets.dataset
                        AND versions.version = assets.asset
                   WHERE assets.asset_type = :asset_type
                    AND assets.status = 'saved'
                    AND versions.is_latest = true
                    AND versions.dataset = :dataset""",
                {"dataset": dataset, "asset_type": asset_type},
            )

        if not latest:
            raise HTTPException(
                status_code=400, detail=f"Dataset {dataset} has no `latest` version.",
            )

        return latest

    return get_latest_version


get_latest_static_version = latest_version_constructor(static_asset)
get_latest_dynamic_version = latest_version_constructor(dynamic_asset)


def field_constructor(asset_type):
    @cached(cache=TTLCache(maxsize=15, ttl=900))
    def get_fields(dataset: str, version: str) -> List[Dict[str, Any]]:
        with get_synchronous_db() as db:
            fields = db.scalar(
                """SELECT DISTINCT
                    metadata->>'fields_'
                   FROM assets
                   WHERE asset_type = :asset_type
                    AND status = 'saved'
                    AND dataset = :dataset
                    AND version = :version""",
                {"dataset": dataset, "version": version, "asset_type": asset_type},
            )

        if not fields:
            raise HTTPException(
                status_code=400,
                detail=f"Dataset {dataset}.{version} has no fields specified.",
            )
        return fields


get_static_fields = field_constructor(static_asset)
get_dynamic_fields = field_constructor(dynamic_asset)
