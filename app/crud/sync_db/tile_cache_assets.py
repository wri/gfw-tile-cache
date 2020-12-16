from typing import Any, Callable, Dict, List, Optional, Tuple

from cachetools import TTLCache, cached
from fastapi.logger import logger

from ...application import get_synchronous_db
from ...models.enumerators.tile_caches import TileCacheType


def dataset_constructor(asset_type: str):
    # @cached(cache=TTLCache(maxsize=15, ttl=900))
    def get_datasets() -> List[str]:
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

    return get_datasets


get_static_vector_tile_cache_dataset: Callable[[], List[str]] = dataset_constructor(
    TileCacheType.static_vector_tile_cache
)
get_dynamic_vector_tile_cache_dataset: Callable[[], List[str]] = dataset_constructor(
    TileCacheType.dynamic_vector_tile_cache
)
get_raster_tile_cache_dataset: Callable[[], List[str]] = dataset_constructor(
    TileCacheType.raster_tile_cache
)


def version_constructor(asset_type: str):
    # memorize fields for 15 min
    # @cached(cache=TTLCache(maxsize=15, ttl=900))
    def get_versions(dataset: str) -> List[Tuple[str, str]]:
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

    return get_versions


get_static_vector_tile_cache_version: Callable[
    [str], List[Tuple[str, str]]
] = version_constructor(TileCacheType.static_vector_tile_cache)
get_dynamic_vector_tile_cache_version: Callable[
    [str], List[Tuple[str, str]]
] = version_constructor(TileCacheType.dynamic_vector_tile_cache)
get_raster_tile_cache_version: Callable[
    [str], List[Tuple[str, str]]
] = version_constructor(TileCacheType.raster_tile_cache)


def latest_version_constructor(asset_type: str):
    # memorize fields for 15 min
    # @cached(cache=TTLCache(maxsize=15, ttl=900))
    def get_latest_version(dataset: str) -> Optional[str]:
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
            logger.warning(
                f"Did not found `latest` version for {asset_type} of {dataset}."
            )
            latest = None
        else:
            latest = row[0]

        return latest

    return get_latest_version


get_latest_static_tile_cache_version: Callable[
    [str], Optional[str]
] = latest_version_constructor(TileCacheType.static_vector_tile_cache)
get_latest_dynamic_tile_cache_version: Callable[
    [str], Optional[str]
] = latest_version_constructor(TileCacheType.dynamic_vector_tile_cache)
get_latest_raster_tile_cache_version: Callable[
    [str], Optional[str]
] = latest_version_constructor(TileCacheType.raster_tile_cache)


def attribute_constructor(asset_type: str):
    # @cached(cache=TTLCache(maxsize=15, ttl=900))
    def get_attributes(dataset: str, version: str) -> List[Dict[str, Any]]:
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

    return get_attributes


get_static_vector_tile_cache_attributes: Callable[
    [str, str], List[Dict[str, Any]]
] = attribute_constructor(TileCacheType.static_vector_tile_cache)
get_dynamic_vector_tile_cache_attributes: Callable[
    [str, str], List[Dict[str, Any]]
] = attribute_constructor(TileCacheType.dynamic_vector_tile_cache)
