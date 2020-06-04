def test_datasets(client):
    """
    Basic test to check if empty data api response as expected
    """

    response = client.get("/nasa_viirs_fire_alerts/latest/dynamic/VectorTileServer")

    assert response.json()["tiles"] == [
        "../{z}/{x}/{y}.pbf?start_date=2020-05-26&end_date=2020-06-02&high_confidence_only=False&force_date_range=False&include_attribute=['latitude', 'longitude', 'alert__date', 'alert__time_utc', 'confidence__cat', 'bright_ti4__k', 'bright_ti5__k', 'frp__mw']"
    ]
