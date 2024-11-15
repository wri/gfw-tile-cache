# mypy: ignore-errors
from urllib.parse import urlparse, urlunparse


def handler(event, context):
    """This function updates the HTTP status code in the response to 307, to
    redirect to another path (cache behavior) that has a different origin
    configured.

    Note the following:
    1. The function is triggered in an origin response
    2. The response status from the origin server is an error status code (404)
    """

    response = event["Records"][0]["cf"]["response"]
    request = event["Records"][0]["cf"]["request"]
    headers = response["headers"]

    # if S3 returns a 404 sets custom origin properties
    # custom origin is tile cache app. URL is passed via custom header set in cloud front
    # (env variables are not support for Lambda@Edge)

    parsed_url = urlparse(request["uri"])
    path_parts = parsed_url.path.split("/")

    if int(response["status"]) == 404 and is_tile(path_parts):
        implementation = replace_implementation(path_parts)

        updated_path = "/".join(path_parts)

        # Append the query string with the `implementation`
        if request["querystring"]:
            querystring = f"{request['querystring']}&implementation={implementation}"
        else:
            querystring = f"implementation={implementation}"

        updated_url = urlunparse(
            parsed_url._replace(path=updated_path, query=querystring)
        )

        # Set the headers for the redirect response
        headers["location"] = [{"key": "Location", "value": updated_url}]
        headers["content-type"] = [{"key": "Content-Type", "value": "application/json"}]
        headers["content-encoding"] = [{"key": "Content-Encoding", "value": "UTF-8"}]

        response = {
            "status": "307",
            "statusDescription": "Temporary Redirect",
            "headers": headers,
        }

    return response


def is_tile(uri):
    print("REQUEST URI", "/".join(uri))
    return len(uri) == 7 and uri[6][-4:] in [".png", ".pbf"]


def replace_implementation(path_parts):
    """Replace the implementation path segment with "dynamic" and return the
    original implementation."""
    impl_path_location = 3
    implementation = path_parts[impl_path_location]
    path_parts[impl_path_location] = "dynamic"
    return implementation


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
