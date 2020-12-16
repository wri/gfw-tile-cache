from app.crud.sync_db.tile_cache_assets import (
    get_dynamic_vector_tile_cache_attributes,
    get_dynamic_vector_tile_cache_dataset,
    get_dynamic_vector_tile_cache_version,
    get_latest_dynamic_tile_cache_version,
    get_latest_static_tile_cache_version,
    get_static_vector_tile_cache_attributes,
    get_static_vector_tile_cache_dataset,
    get_static_vector_tile_cache_version,
)


def test_get_static_datasets():
    result = ["wdpa_protected_areas"]
    assert result == get_static_vector_tile_cache_dataset()


def test_get_dynamic_datasets():
    result = ["nasa_viirs_fire_alerts"]
    assert result == get_dynamic_vector_tile_cache_dataset()


def test_get_static_versions():
    result = ["v201912"]
    assert result == get_static_vector_tile_cache_version("wdpa_protected_areas")


def test_get_dynamic_versions():
    result = ["v202003"]
    assert result == get_dynamic_vector_tile_cache_version("nasa_viirs_fire_alerts")


def test_get_non_existing_versions():
    result = []
    assert result == get_static_vector_tile_cache_version("fails")


def test_get_latest_static_version():
    result = "v201912"
    assert result == get_latest_static_tile_cache_version("wdpa_protected_areas")


def test_get_latest_dynamic_version():
    result = "v202003"
    assert result == get_latest_dynamic_tile_cache_version("nasa_viirs_fire_alerts")


def test_get_latest_non_existing_version():
    assert get_latest_static_tile_cache_version("fails") is None


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
    assert result == get_static_vector_tile_cache_attributes(
        "wdpa_protected_areas", "v201912"
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
    assert result == get_dynamic_vector_tile_cache_attributes(
        "nasa_viirs_fire_alerts", "v202003"
    )


def test_get_non_existing_fields():
    result = []
    assert result == get_static_vector_tile_cache_attributes("fails", "v2")
