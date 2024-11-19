from terraform.modules.content_delivery_network.lambda_functions.redirect_s3_404.src.lambda_function import (
    handler,
)


def create_event(status="404", uri="not important for this test", querystring=""):
    """Helper method to create the base event dictionary with customizable
    status, URI, and query string."""
    return {
        "Records": [
            {
                "cf": {
                    "response": {
                        "status": status,
                        "headers": {
                            "content-type": [
                                {"key": "Content-Type", "value": "application/json"}
                            ]
                        },
                    },
                    "request": {
                        "uri": uri,
                        "querystring": querystring,
                    },
                }
            }
        ]
    }


class TestRedirectOnlyTileRequestsThatAreNotFound:
    def test_handler_does_not_modify_response_if_status_is_something_other_than_404(
        self,
    ):
        event = create_event(status="200")
        context = {}

        response = handler(event, context)

        assert response == {
            "status": "200",
            "headers": {
                "content-type": [{"key": "Content-Type", "value": "application/json"}]
            },
        }

    def test_handler_creates_a_redirect_response_if_status_is_404_and_is_a_tile(self):
        event = create_event(
            uri="/sbtn_natural_forests_map/v202310/natural_forest/10/20/30.png"
        )
        context = {}

        response = handler(event, context)

        assert (
            response.items()
            >= {
                "status": "307",
                "statusDescription": "Temporary Redirect",
            }.items()
        )

    def test_handler_does_not_modify_response_if_request_is_a_resource_other_than_a_tile(
        self,
    ):
        event = create_event(
            uri="/sbtn_natural_forests_map/v202310/natural_forest/10/20/30.txt"
        )
        context = {}

        response = handler(event, context)

        assert response == {
            "status": "404",
            "headers": {
                "content-type": [{"key": "Content-Type", "value": "application/json"}]
            },
        }


def test_handler():
    # Mock event and context
    event = {
        "Records": [
            {
                "cf": {
                    "response": {
                        "status": "404",
                        "headers": {
                            "content-type": [
                                {"key": "Content-Type", "value": "text/plain"}
                            ]
                        },
                    },
                    "request": {
                        "uri": "/sbtn_natural_forests_map/v202310/natural_forest/10/20/30.png",
                        "querystring": "some_param=30",
                    },
                }
            }
        ]
    }
    context = {}

    # Call the handler function
    response = handler(event, context)

    # Assertions
    assert response["status"] == "307"
    assert response["headers"]["location"][0]["key"] == "Location"
    assert (
        response["headers"]["location"][0]["value"]
        == "/sbtn_natural_forests_map/v202310/dynamic/10/20/30.png?some_param=30&implementation=natural_forest"
    )
    assert response["headers"]["content-type"][0]["value"] == "application/json"
