def test_allow_all_route(client):
    response = client.get("/", headers={"Origin": "https://www.test.com"})
    assert response.headers.get("access-control-allow-origin") == "*"

    response = client.get("/planet/v1", headers={"Origin": "https://www.test.com"})
    assert response.headers.get("access-control-allow-origin") is None

    response = client.get(
        "/planet/v1", headers={"Origin": "https://www.globalforestwatch.org"}
    )
    assert (
        response.headers.get("access-control-allow-origin")
        == "https://www.globalforestwatch.org"
    )
