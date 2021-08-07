import pytest

from app.routes.preview import get_default_style_spec


@pytest.mark.skip(reason="Need to set up s3 mocking")
def test_tile_cache_preview(client):
    """
    Test tile cache preview page returns success response
    """

    datasets = ["wdpa_protected_areas", "umd_glad_landsat_alerts"]
    versions = ["v201912", "v20210101"]

    response = client.get(f"/{datasets[0]}/{versions[0]}/default/preview")
    assert response.status_code == 200

    response = client.get(f"/{datasets[1]}/{versions[1]}/default/preview")
    assert response.status_code == 200


# test helper functions
def test_generate_default_mapbox_style():
    tile = {
        "dataset": "umd_glad_landsat_alerts",
        "version": "v20210101",
        "implementation": "default",
        "is_latest": True,
        "fields": [],
        "min_zoom": 0,
        "max_zoom": 12,
        "min_date": None,
        "max_date": None,
        "asset_type": "Raster tile cache",
        "asset_uri": "my_uri7",
    }

    mapbox_style = get_default_style_spec(tile)

    assert mapbox_style["source"] == {"type": "raster", "tiles": ["my_uri7"]}

    assert mapbox_style["layer"] == {
        "id": "umd_glad_landsat_alerts-layer",
        "type": "raster",
        "source": "umd_glad_landsat_alerts",
        "minzoom": 0,
        "maxzoom": 12,
        "source_layer": "umd_glad_landsat_alerts",
    }
