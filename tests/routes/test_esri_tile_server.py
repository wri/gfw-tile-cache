def test_viirs_vector_tile_server(client):
    """
    Basic test to check if empty data api response as expected
    """

    response = client.get("/nasa_viirs_fire_alerts/latest/dynamic/VectorTileServer")
    assert response.json() == {
        "detail": "You must list version name explicitly for this operation."
    }

    response = client.get("/nasa_viirs_fire_alerts/v202003/dynamic/VectorTileServer")

    assert response.json()["tiles"] == ["../{z}/{x}/{y}@0.25x.pbf"]

    response = client.get(
        "/nasa_viirs_fire_alerts/v202003/dynamic/2020-05-26/2020-06-02/VectorTileServer"
    )

    assert response.json()["tiles"] == [
        "../../../{z}/{x}/{y}@0.25x.pbf?start_date=2020-05-26&end_date=2020-06-02"
    ]
