from app.crud.sync_db.tile_cache_assets import (
    get_attributes,
    get_datasets,
    get_latest_version,
    get_versions,
)
from app.models.enumerators.tile_caches import TileCacheType


def test_get_static_datasets():
    result = ["wdpa_protected_areas"]
    assert result == get_datasets(TileCacheType.static_vector_tile_cache)


def test_get_dynamic_datasets():
    result = ["nasa_viirs_fire_alerts"]
    assert result == get_datasets(TileCacheType.dynamic_vector_tile_cache)


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
