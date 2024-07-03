import pytest

from ..conftest import parse_img


@pytest.mark.asyncio
async def test_tile_for_data_api_dataset(client):
    response = client.get(
        "/cog/basic/tiles/WebMercatorQuad/8/87/48?dataset=umd_glad_landsat_alerts&version=v20210101"
    )
    response.status_code == 200

    assert response.headers["content-type"] == "image/jpeg"
    meta = parse_img(response.content)
    assert meta["width"] == 256
    assert meta["height"] == 256


@pytest.mark.asyncio
async def test_tiling_with_custom_rendering(client):
    """Test Integrated Alerts Tile Rendering."""
    response = client.get(
        "/cog/custom/tiles/WebMercatorQuad/14/5305/8879?url=s3://gfw-data-lake-test&bands=default&bands=intensity&algorithm=integrated_alerts&return_mask=False&format=png"
    )
    response.status_code == 200

    assert response.headers["content-type"] == "image/png"
    meta = parse_img(response.content)
    assert meta["width"] == 256
    assert meta["height"] == 256
