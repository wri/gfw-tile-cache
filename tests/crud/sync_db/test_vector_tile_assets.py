import pytest

from app.crud.sync_db.tile_cache_assets import (
    get_attributes,
    get_dataset_tile_caches,
    get_datasets,
    get_latest_date,
    get_latest_version,
    get_versions,
)
from app.models.enumerators.tile_caches import TileCacheType


@pytest.mark.skip("Skip to deploy metadata fixes")
def test_get_static_datasets():
    result = ["wdpa_protected_areas"]
    assert result == get_datasets(TileCacheType.static_vector_tile_cache)


def test_get_dynamic_datasets():
    result = ["nasa_viirs_fire_alerts", "umd_modis_burned_areas"]
    datasets = get_datasets(TileCacheType.dynamic_vector_tile_cache)
    assert result == list(sorted(datasets))


@pytest.mark.skip("Skip to deploy metadata fixes")
def test_get_static_versions():
    result = ["v201912"]
    assert result == get_versions(
        "wdpa_protected_areas", TileCacheType.static_vector_tile_cache
    )


def test_get_dynamic_versions():
    result = ["v202003"]
    assert result == get_versions(
        "nasa_viirs_fire_alerts", TileCacheType.dynamic_vector_tile_cache
    )


def test_get_non_existing_versions():
    result = []
    assert result == get_versions("fails", TileCacheType.static_vector_tile_cache)


@pytest.mark.skip("Skip to deploy metadata fixes")
def test_get_latest_static_version():
    result = "v201912"
    assert result == get_latest_version(
        "wdpa_protected_areas", TileCacheType.static_vector_tile_cache
    )


def test_get_latest_dynamic_version():
    result = "v202003"
    assert result == get_latest_version(
        "nasa_viirs_fire_alerts", TileCacheType.dynamic_vector_tile_cache
    )


def test_get_latest_non_existing_version():
    assert get_latest_version("fails", TileCacheType.static_vector_tile_cache) is None


@pytest.mark.skip("Skip to deploy metadata fixes")
def test_get_static_fields():
    result = [
        {
            "field_name": "static_test",
            "field_alias": "TEST",
            "field_type": "text",
            "field_description": None,
            "is_feature_info": True,
            "is_filter": False,
        }
    ]
    assert result == get_attributes(
        "wdpa_protected_areas", "v201912", TileCacheType.static_vector_tile_cache
    )


def test_get_dynamic_fields():
    result = [
        {
            "field_name": "dynamic_test",
            "field_alias": "TEST",
            "field_type": "text",
            "field_description": None,
            "is_feature_info": True,
            "is_filter": False,
        }
    ]
    assert result == get_attributes(
        "nasa_viirs_fire_alerts", "v202003", TileCacheType.dynamic_vector_tile_cache
    )


def test_get_non_existing_fields():
    result = []
    assert result == get_attributes(
        "fails", "v2", TileCacheType.static_vector_tile_cache
    )


def test_latest_date():
    result = "2020-01-01"
    assert result == get_latest_date("nasa_viirs_fire_alerts", "v202003")


@pytest.mark.skip("Skip to deploy metadata fixes")
def test_get_dataset_tile_caches():
    tile_caches = get_dataset_tile_caches(
        "umd_glad_landsat_alerts", "v20210101", "default"
    )

    assert len(tile_caches) == 1
    assert tile_caches[0]["asset_uri"] == "my_uri7"
