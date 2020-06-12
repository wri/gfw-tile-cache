from fastapi import HTTPException

from app.crud.vector_tile_assets import (
    get_dynamic_datasets,
    get_dynamic_fields,
    get_dynamic_versions,
    get_latest_dynamic_version,
    get_latest_static_version,
    get_static_datasets,
    get_static_fields,
    get_static_versions,
)


def test_get_static_datasets():
    result = ["wdpa_protected_areas"]
    assert result == get_static_datasets()


def test_get_dynamic_datasets():
    result = ["nasa_viirs_fire_alerts"]
    assert result == get_dynamic_datasets()


def test_get_static_versions():
    result = ["v201912"]
    assert result == get_static_versions("wdpa_protected_areas")


def test_get_dynamic_versions():
    result = ["v202003"]
    assert result == get_dynamic_versions("nasa_viirs_fire_alerts")


def test_get_non_existing_versions():
    response = ""
    status_code = "200"
    try:
        get_static_versions("fails")
    except HTTPException as e:
        response = str(e.detail)
        status_code = str(e.status_code)
    assert response == "Dataset `fails` has no dynamic tile cache."
    assert status_code == "400"


def test_get_latest_static_version():
    result = "v201912"
    assert result == get_latest_static_version("wdpa_protected_areas")


def test_get_latest_dynamic_version():
    result = "v202003"
    assert result == get_latest_dynamic_version("nasa_viirs_fire_alerts")


def test_get_latest_non_existing_version():
    response = ""
    status_code = "200"
    try:
        get_latest_static_version("fails")
    except HTTPException as e:
        response = str(e.detail)
        status_code = str(e.status_code)
    assert response == "Dataset `fails` has no `latest` version."
    assert status_code == "400"


def test_get_static_fields():
    result = []
    assert result == get_static_fields("wdpa_protected_areas", "v201912")


def test_get_dynamic_fields():
    result = []
    assert result == get_dynamic_fields("nasa_viirs_fire_alerts", "v202003")


def test_get_non_existing_fields():
    response = ""
    status_code = "200"
    try:
        get_static_fields("fails", "v2")
    except HTTPException as e:
        response = str(e.detail)
        status_code = str(e.status_code)
    assert response == "Dataset `fails.v2` has no fields specified."
    assert status_code == "400"
