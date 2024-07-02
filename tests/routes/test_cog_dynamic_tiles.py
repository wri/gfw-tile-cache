import pytest

from ..conftest import parse_img


@pytest.mark.asyncio
async def test_cog_for_data_api_dataset(client):
    response = client.get(
        "/cog/basic/tiles/WebMercatorQuad/8/87/48?dataset=umd_glad_landsat_alerts&version=v20210101"
    )
    response.status_code == 200

    assert response.headers["content-type"] == "image/jpeg"
    meta = parse_img(response.content)
    assert meta["width"] == 256
    assert meta["height"] == 256


# TODO add integrated alerts test
