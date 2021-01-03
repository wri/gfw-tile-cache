from PIL import Image
from io import BytesIO
import numpy as np
import boto3
import pytest


@pytest.mark.parametrize("x, y, multiplier", [(0, 0, 1), (1, 1, 4)])
def test_dynamic_tiles(x, y, multiplier, client):
    """
    Test dynamic tile cache
    :param x: x block coordinate for tile
    :param y: y block coordinate for tile
    :param multiplier: the test tile has multiplier for each x, y block. This is used to check the expected result values.
    """
    try:
        response = client.get(f"/wur_radd_alerts/v20201214/dynamic/14/{x}/{y}.png", stream=True)
        assert response.status_code == 200

        response.raw.decode_content = True
        image_bytes = BytesIO()
        for chunk in response:
            image_bytes.write(chunk)

        image_bytes.seek(0)
        _check_png(image_bytes, multiplier)

        # check if s3 file copied
        saved_bytes = BytesIO()
        s3_client = boto3.client("s3", endpoint_url="http://localstack:4566")
        s3_client.download_fileobj("gfw-tiles-test", f"wur_radd_alerts/v20201214/dynamic/14/{x}/{y}.png", saved_bytes)
        saved_bytes.seek(0)
        _check_png(saved_bytes, multiplier)
    finally:
        log_client = boto3.client("logs", region_name="us-east-1", endpoint_url="http://localstack:4566")
        log_group_name = "/aws/lambda/test_project-lambda-tiler"
        for log_stream in log_client.describe_log_streams(logGroupName=log_group_name)[
            "logStreams"
        ]:
            log_events = log_client.get_log_events(
                logGroupName=log_group_name, logStreamName=log_stream["logStreamName"],
            )["events"]

            for event in log_events:
                # for some reason stack traces come with carriage returns,
                # which overwrites the line instead of making a new line
                message = event["message"].replace("\r", "\n")
                print(f"{log_stream['logStreamName']}: {message}")


def _check_png(image_bytes, multiplier):
    image = Image.open(image_bytes)
    rgba = np.array(image)
    assert rgba.shape == (256, 256, 4)
    assert np.all(rgba[:, :, 0] == 1 * multiplier)
    assert np.all(rgba[:, :, 1] == 2 * multiplier)
    assert np.all(rgba[:, :, 2] == 3 * multiplier)
    assert np.all(rgba[:, :, 3] == 4 * multiplier)