from typing import Dict, List, Optional

import pendulum
from cachetools import TTLCache, cached
from fastapi.logger import logger
from pendulum import Duration

from ...application import get_synchronous_db
from ...models.enumerators.tile_caches import TileCacheType
from ...utils.data_api import get_version_fields


@cached(cache=TTLCache(maxsize=1, ttl=900))
def get_all_tile_caches():

    tile_caches: Dict[str, List] = {e.value: list() for e in list(TileCacheType)}

    with get_synchronous_db() as db:
        rows = db.execute(
            f"""SELECT DISTINCT
                    assets.asset_type as asset_type,
                    assets.asset_uri as asset_uri,
                    versions.dataset as dataset,
                    versions.version as version,
                    assets.creation_options->'implementation' as implementation,
                    versions.is_latest as is_latest,
                    assets.creation_options->'min_zoom' as min_zoom,
                    assets.creation_options->'max_zoom' as max_zoom,
                    version_metadata.content_start_date as min_date,
                    version_metadata.content_end_date as max_date
                   FROM assets
                    JOIN versions
                    ON versions.dataset = assets.dataset
                        AND versions.version = assets.version
                    LEFT JOIN version_metadata
                    ON versions.dataset = version_metadata.dataset
                        AND versions.version = version_metadata.version
                   WHERE assets.asset_type IN {str(tuple([e.value for e in list(TileCacheType)])).replace('"', "'")}
                    AND assets.status = 'saved'"""
        ).fetchall()

    if rows is None or len(rows) == 0:
        logger.warning(
            "No rows returned. There are no tile caches registered with the API"
        )
        rows = []

    for row in rows:
        tile_caches[row.asset_type].append(
            {
                "dataset": row.dataset,
                "version": row.version,
                "implementation": row.implementation,
                "is_latest": row.is_latest,
                "min_zoom": row.min_zoom,
                "max_zoom": row.max_zoom,
                "min_date": row.min_date.strftime("%Y-%m-%d")
                if row.min_date is not None
                else None,
                "max_date": row.max_date.strftime("%Y-%m-%d")
                if row.max_date is not None
                else None,
                "asset_uri": row.asset_uri,
                "asset_type": row.asset_type,
            }
        )

    return tile_caches


# @cached(cache=TTLCache(maxsize=15, ttl=900))
def get_datasets(asset_type: str) -> List[str]:
    tile_caches = get_all_tile_caches()

    datasets = {tile_cache["dataset"] for tile_cache in tile_caches[asset_type]}

    return list(datasets)


# @cached(cache=TTLCache(maxsize=15, ttl=900))
def get_versions(dataset: str, asset_type: str) -> List[str]:
    tile_caches = get_all_tile_caches()
    versions = {
        tile_cache["version"]
        for tile_cache in tile_caches[asset_type]
        if tile_cache["dataset"] == dataset
    }

    return list(versions)


# @cached(cache=TTLCache(maxsize=15, ttl=900))
def get_latest_version(dataset: str, asset_type: str) -> Optional[str]:
    tile_caches = get_all_tile_caches()

    for tile_cache in tile_caches[asset_type]:
        if tile_cache["dataset"] == dataset and tile_cache["is_latest"]:
            return tile_cache["version"]

    logger.warning(f"Did not found `latest` version for {asset_type} of {dataset}.")
    return None


@cached(cache=TTLCache(maxsize=1, ttl=900))
def get_latest_versions() -> List[Dict[str, str]]:
    tile_caches = get_all_tile_caches()
    _latest_versions = [
        {"dataset": tile_cache["dataset"], "version": tile_cache["version"]}
        for e in list(TileCacheType)
        for tile_cache in tile_caches[e.value]
        if tile_cache["is_latest"]
    ]

    # the above my return duplicates from different tile cache types
    # To deduplicate, we cannot use sets due to the dicts inside the list
    latest_versions = list()
    for latest_version in _latest_versions:
        if latest_version not in latest_versions:
            latest_versions.append(latest_version)

    if not latest_versions:
        logger.warning("There are no latest versions registered with the API.")

    return latest_versions


async def get_attributes(dataset, version):
    # TODO: fetch the correct one for the current implementation
    #  needs changes to data-api to assure dynamic vector tile caches
    #  also have the implementation parameter in the creation options
    return await get_version_fields(dataset, version)


@cached(cache=TTLCache(maxsize=100, ttl=900))
def get_max_zoom(
    dataset: str, version: str, implementation: str, asset_type: str
) -> Optional[int]:
    tile_caches = get_all_tile_caches()
    for tile_cache in tile_caches[asset_type]:
        if (
            tile_cache["dataset"] == dataset
            and tile_cache["version"] == version
            and tile_cache["implementation"] == implementation
        ):
            return tile_cache["max_zoom"]

    return None


@cached(cache=TTLCache(maxsize=100, ttl=900))
def get_implementations(dataset: str, version: str, asset_type: str) -> List[str]:
    tile_caches = get_all_tile_caches()

    implementations = [
        tile_cache["implementation"]
        for tile_cache in tile_caches[asset_type]
        if (tile_cache["dataset"] == dataset and tile_cache["version"] == version)
    ]
    return implementations


@cached(cache=TTLCache(maxsize=100, ttl=900))
def get_dataset_tile_caches(
    dataset: str, version: str, implementation: str
) -> List[Dict]:
    tile_caches = get_all_tile_caches()
    tile_caches_list: List[Dict] = sum(
        list(tile_caches.values()), []
    )  # merging all tile cache type values

    dataset_tile_caches = [
        tile_cache
        for tile_cache in tile_caches_list
        if tile_cache["dataset"] == dataset
        and tile_cache["version"] == version
        and tile_cache["implementation"]
    ]

    return dataset_tile_caches


@cached(cache=TTLCache(maxsize=100, ttl=86400))
def get_latest_date(schema, version=None):
    tile_caches = get_all_tile_caches()

    for asset_type_caches in tile_caches.values():
        for tile_cache in asset_type_caches:
            if tile_cache["dataset"] == schema:
                if version and tile_cache["version"] == version:
                    return tile_cache["max_date"]
                elif not version and tile_cache["is_latest"]:
                    return tile_cache["max_date"]

    return None


def default_start(schema: str, delta: Duration):
    end_date = pendulum.parse(default_end(schema))
    return end_date.subtract(days=delta.days).to_date_string()


def default_end(schema):
    latest_date = get_latest_date(schema)
    return latest_date if latest_date else pendulum.now().to_date_string()
