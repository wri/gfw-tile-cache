import pytest


@pytest.mark.parametrize("z, x, y", [(2, 3, 3), (8, 10, 10)])
def test_umd_modis_burned_areas(z, x, y, client):
    """Test dynamic tile cache.

    :param x: x block coordinate for tile
    :param y: y block coordinate for tile
    :param multiplier: the test tile has multiplier for each x, y block. This is used to check the expected result values.
    """
    with client.stream(
        "GET",
        f"/umd_modis_burned_areas/v202003/dynamic/{z}/{x}/{y}.pbf",
        params={
            "start_date": "2019-01-01",
            "end_date": "2019-06-01",
            "force_date_range": True,
        },
    ) as response:
        assert (
            response.status_code == 200
        ), f"Bad response for request {response.request.url}: {response.json()}"
