from typing import Any, Dict, List, Optional

from cachetools import TTLCache, cached
from fastapi.logger import logger

from ...application import get_synchronous_db
from ...models.enumerators.tile_caches import TileCacheType


@cached(cache=TTLCache(maxsize=1, ttl=900))
def get_all_tile_caches():

    tile_caches: Dict[str, List] = {e.value: list() for e in list(TileCacheType)}

    with get_synchronous_db() as db:
        rows = db.execute(
            f"""SELECT DISTINCT
                    assets.asset_type as asset_type,
                    versions.dataset as dataset,
                    versions.version as version,
                    assets.creation_options->'implementation' as implementation,
                    versions.is_latest as is_latest,
                    assets.fields as fields,
                    assets.creation_options->'min_zoom' as min_zoom,
                    assets.creation_options->'max_zoom' as max_zoom
                   FROM versions
                    JOIN assets
                    ON versions.dataset = assets.dataset
                        AND versions.version = assets.version
                   WHERE assets.asset_type IN {str(tuple([e.value for e in list(TileCacheType)])).replace('"', "'")}
                    AND assets.status = 'saved'"""
        ).fetchall()
    if not rows:
        # tile_caches = []
        logger.warning("There are no tile caches registered with the API.")
    # else:
    # tile_caches = rows

    for row in rows:
        tile_caches[row.asset_type].append(
            {
                "dataset": row.dataset,
                "version": row.version,
                "implementation": row.implementation,
                "is_latest": row.is_latest,
                "fields": row.fields,
                "min_zoom": row.min_zoom,
                "max_zoom": row.max_zoom,
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


@cached(cache=TTLCache(maxsize=15, ttl=900))
def get_attributes(dataset: str, version: str, asset_type: str) -> List[Dict[str, Any]]:
    tile_caches = get_all_tile_caches()

    for tile_cache in tile_caches[asset_type]:
        # pick the first one that matchs
        # TODO: fetch the correct one for the current implementation
        #  needs changes to data-api to assure dynamic vector tile caches
        #  also have the implementation parameter in the creation options
        if tile_cache["dataset"] == dataset and tile_cache["version"] == version:
            return tile_cache["fields"]

    logger.warning(
        f"Did not find any fields in metadata for {asset_type} of {dataset}.{version}."
    )
    return list()


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
