from unittest.mock import patch

import pytest

from lambdas.raster_tiler.lambda_function import handler
from tests.conftest import TEST_PNG
from tests.fixtures.payloads import umd_glad_alerts_payload, umd_tree_cover_loss_payload


@pytest.mark.parametrize(
    "params, payload", [umd_tree_cover_loss_payload(), umd_glad_alerts_payload()]
)
@patch("lambdas.raster_tiler.lambda_function.urlopen")
def test_handler(mock_url, params, payload):
    mock_url.return_value = TEST_PNG
    response = handler(payload, {})

    assert response["status"] == "success"