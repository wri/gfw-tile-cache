# mypy: ignore-errors
from urllib.parse import urlparse, urlunparse


def handler(event, context):
    """This function updates the HTTP status code in the response to 307, to
    redirect to another path (cache behavior) that has a different origin
    configured.

    Note the following:
    1. The function is triggered in an origin response
    2. The response status from the origin server is an error status code (404)

    The pattern for the incoming request uri:

    /{dataset}/{version}/{implementation}/{z}/{x}/{y}.(png|pbf)

    results in a redirect response like:

    /{dataset}/{version}/dynamic/{z}/{x}/{y}.(png|pbf)?implementation={implementation}
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
        implementation = replace_implementation_in_path(path_parts)
        querystring = add_implementation_to_query_params(
            implementation, request["querystring"]
        )
        updated_url = urlunparse(
            parsed_url._replace(path="/".join(path_parts), query=querystring)
        )
        update_headers_for_redirect(headers, updated_url)
        return build_redirect_response(headers)

    return response


def is_tile(uri):
    """The resource is a tile if its last path element ends in .png or .pbf."""
    print("REQUEST URI", "/".join(uri))
    return len(uri) == 7 and uri[6][-4:] in [".png", ".pbf"]


def replace_implementation_in_path(path_parts):
    """Replace the implementation path segment with "dynamic" and return the
    original implementation."""
    implementation = path_parts[3]
    path_parts[3] = "dynamic"
    return implementation


def add_implementation_to_query_params(implementation, query_string):
    implementation_param = f"implementation={implementation}"
    if query_string:
        querystring = f"{query_string}&{implementation_param}"
    else:
        querystring = implementation_param
    return querystring


def update_headers_for_redirect(headers, updated_url):
    headers["location"] = [{"key": "Location", "value": updated_url}]
    headers["content-type"] = [{"key": "Content-Type", "value": "application/json"}]
    headers["content-encoding"] = [{"key": "Content-Encoding", "value": "UTF-8"}]


def build_redirect_response(headers):
    response = {
        "status": "307",
        "statusDescription": "Temporary Redirect",
        "headers": headers,
    }
    return response
