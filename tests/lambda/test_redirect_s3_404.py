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

        response = handler(event, {})

        assert response == {
            "status": "200",
            "headers": {
                "content-type": [{"key": "Content-Type", "value": "application/json"}]
            },
        }

    def test_handler_creates_a_redirect_response_if_status_is_404_and_is_a_png_tile(
        self,
    ):
        event = create_event(
            uri="/sbtn_natural_forests_map/v202310/natural_forest/10/20/30.png"
        )

        response = handler(event, {})

        assert (
            response.items()
            >= {
                "status": "307",
                "statusDescription": "Temporary Redirect",
            }.items()
        )

    def test_handler_creates_a_redirect_response_if_status_is_404_and_is_a_pbf_tile(
        self,
    ):
        event = create_event(
            uri="/sbtn_natural_forests_map/v202310/natural_forest/10/20/30.pbf"
        )

        response = handler(event, {})

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

        response = handler(event, {})

        assert response == {
            "status": "404",
            "headers": {
                "content-type": [{"key": "Content-Type", "value": "application/json"}]
            },
        }


class TestRedirectsToADynamicTileResource:
    def test_original_implementation_is_replaced_with_dynamic(self):
        implementation = "natural_forest"
        event = create_event(
            uri=f"/sbtn_natural_forests_map/v202310/{implementation}/10/20/30.png"
        )

        response = handler(event, {})

        assert response["headers"]["location"][0]["key"] == "Location"
        assert (
            "/sbtn_natural_forests_map/v202310/dynamic/10/20/30.png"
            in response["headers"]["location"][0]["value"]
        )


class TestAddsOriginalImplementationToTheExistingQueryParams:
    def test_original_implementation_is_added_to_the_list_of_query_parameters(self):
        implementation = "natural_forest"
        event = create_event(
            uri=f"/sbtn_natural_forests_map/v202310/{implementation}/10/20/30.png",
            querystring="some_param=30",
        )

        response = handler(event, {})

        assert response["headers"]["location"][0]["key"] == "Location"
        assert (
            "?some_param=30&implementation=natural_forest"
            in response["headers"]["location"][0]["value"]
        )

    def test_original_implementation_is_added_as_a_query_parameter(self):
        implementation = "natural_forest"
        event = create_event(
            uri=f"/sbtn_natural_forests_map/v202310/{implementation}/10/20/30.png"
        )

        response = handler(event, {})

        assert response["headers"]["location"][0]["key"] == "Location"
        assert (
            "?implementation=natural_forest"
            in response["headers"]["location"][0]["value"]
        )


class TestStandardHeaderInfoIsAddedToRedirect:
    def test_content_type_is_set(self):
        event = create_event(
            uri="/sbtn_natural_forests_map/v202310/default/10/20/30.png"
        )

        response = handler(event, {})

        assert response["headers"]["content-type"] == [
            {"key": "Content-Type", "value": "application/json"}
        ]

    def test_content_encoding_is_set(self):
        event = create_event(
            uri="/sbtn_natural_forests_map/v202310/default/10/20/30.png"
        )

        response = handler(event, {})

        assert response["headers"]["content-encoding"] == [
            {"key": "Content-Encoding", "value": "UTF-8"}
        ]
