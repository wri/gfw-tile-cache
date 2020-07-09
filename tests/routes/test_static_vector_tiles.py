def test_static_vector_tiles(client):
    response = client.get("/wdpa_protected_areas/v201912/default/1/1/1.pbf")
    assert response.status_code == 501
