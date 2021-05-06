from unittest.mock import patch

import pytest

from lambdas.raster_tiler.lambda_function import handler
from tests.conftest import TEST_PNG
from tests.fixtures.payloads import umd_glad_alerts_payload, umd_tree_cover_loss_payload


@pytest.mark.parametrize(
    "params, payload",
    [
        umd_tree_cover_loss_payload(),
        umd_glad_alerts_payload(),
        umd_tree_cover_loss_payload(z=13),
        umd_glad_alerts_payload(z=15),
    ],
)
@patch("lambdas.raster_tiler.lambda_function.urlopen")
def test_handler(mock_url, params, payload):
    mock_url.return_value = TEST_PNG
    response = handler(payload, {})
    print(response)
    assert response["status"] == "success"
