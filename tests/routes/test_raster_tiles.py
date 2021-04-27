import json
from io import BytesIO
from unittest import mock

import boto3
import numpy as np
import pytest
from PIL import Image

from ..conftest import AWS_ENDPOINT_URI
from ..fixtures.payloads import umd_glad_alerts_payload, umd_tree_cover_loss_payload


@pytest.mark.e2e
@pytest.mark.parametrize("x, y, multiplier", [(0, 0, 1), (1, 1, 4)])
def test_dynamic_tiles_no_params(x, y, multiplier, client):
    """
    Test dynamic tile cache
    :param x: x block coordinate for tile
    :param y: y block coordinate for tile
    :param multiplier: the test tile has multiplier for each x, y block. This is used to check the expected result values.
    """
    try:
        response = client.get(
            f"/wur_radd_alerts/v20201214/dynamic/14/{x}/{y}.png",
            params={"implementation": "default"},
            stream=True,
        )

        assert (
            response.status_code == 200
        ), f"Bad response for request {response.request.url}: {response.json()}"

        img = _response_to_img(response)
        _check_png(img, multiplier)

        # check if s3 file copied. It should now be accessible using the default endpoint.
        saved_bytes = BytesIO()
        s3_client = boto3.client("s3", endpoint_url=AWS_ENDPOINT_URI)
        s3_client.download_fileobj(
            "gfw-tiles-test",
            f"wur_radd_alerts/v20201214/default/14/{x}/{y}.png",
            saved_bytes,
        )
        saved_bytes.seek(0)
        _check_png(saved_bytes, multiplier)
    finally:
        _get_logs()


@pytest.mark.e2e
@pytest.mark.parametrize("x, y, confirmed_only", [(0, 0, False), (0, 0, True)])
def test_dynamic_tiles_params(x, y, confirmed_only, client):
    """
    Test dynamic tile cache end to end
    """
    try:
        response = client.get(
            f"/wur_radd_alerts/v20201214/dynamic/14/{x}/{y}.png",
            params={"confirmed_only": confirmed_only},
            stream=True,
        )

        assert (
            response.status_code == 200
        ), f"Bad response for request {response.request.url}: {response.json()}"

        img = _response_to_img(response)
        _check_filtered_png(img, confirmed_only)

        # check if s3 file copied. It should now be accessible using the default endpoint.
        # saved_bytes = BytesIO()
        # s3_client = boto3.client("s3", endpoint_url=AWS_ENDPOINT_URI)
        # s3_client.download_fileobj(
        #     "gfw-tiles-test",
        #     f"wur_radd_alerts/v20201214/default/14/{x}/{y}.png",
        #     saved_bytes,
        # )
        # saved_bytes.seek(0)
        # _check_png(saved_bytes, multiplier)
    finally:
        _get_logs()


@pytest.mark.parametrize(
    "params, payload", [umd_tree_cover_loss_payload(), umd_glad_alerts_payload()]
)
def test_dynamic_tiles_named(params, payload, client, mock_get_dynamic_tile):
    """Only testing if payload is correctly forwarded to lambda.
    Lambda execution should be handled by a separate test.
    """
    dataset = payload["dataset"]
    version = payload["version"]
    x = payload["x"]
    y = payload["y"]
    z = payload["z"]

    print(payload)

    # This will mock the lambda function and return the payload
    mock_patch = f"app.routes.{dataset}.raster_tiles.get_cached_response"
    with mock.patch(mock_patch) as mck:
        mck.side_effect = mock_get_dynamic_tile

        response = client.get(
            f"/{dataset}/{version}/dynamic/{z}/{x}/{y}.png", params=params, stream=True
        )

        assert (
            response.status_code == 200
        ), f"Bad response for request {response.request.url}: {response.json()}"

        expected_response = {"data": payload, "status": "success"}

        rsp = _response_to_img(response)
        assert json.loads(rsp.read()) == expected_response


def _response_to_img(response):
    response.raw.decode_content = True
    image_bytes = BytesIO()
    for chunk in response:
        image_bytes.write(chunk)

    image_bytes.seek(0)
    return image_bytes


def _check_png(image_bytes, multiplier):
    image = Image.open(image_bytes)
    rgb = np.array(image)
    assert rgb.shape == (256, 256, 3)
    assert np.all(rgb[:, :, 0] == 1 * multiplier)
    assert np.all(rgb[:, :, 1] == 2 * multiplier)
    assert np.all(rgb[:, :, 2] == 3 * multiplier)


def _check_filtered_png(image_bytes, confirmed_only):
    image = Image.open(image_bytes)
    rgba = np.array(image)
    assert rgba.shape == (256, 256, 4)
    assert np.all(rgba[:, :, 0] == 228)
    assert np.all(rgba[:, :, 1] == 102)
    assert np.all(rgba[:, :, 2] == 153)
    if confirmed_only:
        assert np.all(rgba[:, :, 3] == 0)
    else:
        assert np.all(rgba[:, :, 3] == 150)


def _get_logs():
    log_client = boto3.client(
        "logs", region_name="us-east-1", endpoint_url=AWS_ENDPOINT_URI
    )
    log_group_name = "/aws/lambda/test_project-lambda-tiler"
    for log_stream in log_client.describe_log_streams(logGroupName=log_group_name)[
        "logStreams"
    ]:
        log_events = log_client.get_log_events(
            logGroupName=log_group_name,
            logStreamName=log_stream["logStreamName"],
        )["events"]

        for event in log_events:
            # for some reason stack traces come with carriage returns,
            # which overwrites the line instead of making a new line
            message = event["message"].replace("\r", "\n")
            print(f"{log_stream['logStreamName']}: {message}")
