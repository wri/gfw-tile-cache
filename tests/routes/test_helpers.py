def test_viirs_vector_tile_server(client):
    """
    Basic test to check if empty data api response as expected
    """

    response = client.get("/_latest")
    assert response.json() == {
        "data": [
            {"dataset": "nasa_viirs_fire_alerts", "version": "v202003"},
            {"dataset": "umd_glad_alerts", "version": "v20210101"},
            {"dataset": "umd_tree_cover_loss", "version": "v1.8"},
            {"dataset": "wdpa_protected_areas", "version": "v201912"},
            {"dataset": "wur_radd_alerts", "version": "v20201214"},
        ],
        "status": "success",
    }
