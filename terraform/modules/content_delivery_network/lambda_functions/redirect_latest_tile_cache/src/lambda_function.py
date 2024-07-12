# mypy: ignore-errors

import json
import urllib.request
from urllib.parse import parse_qs

LATEST_VERSIONS = None


def get_latest_versions(url):
    """Get latest version for all datasets in Data API Use in memory object if
    exists, otherwise fetch from API B/C this is a Lambd@Edge function I cannot
    connect to a database inside VPC I also cannot read from S3, b/c I cannot
    set ENV variable to indicate the environment I am in Nor can I add a custom
    header to pass in variables b/c this is a viewer-request event-type The
    only option I have is to fetch the request URI and use it for my
    purposes."""
    global LATEST_VERSIONS

    if not LATEST_VERSIONS:
        with urllib.request.urlopen(url) as response:
            LATEST_VERSIONS = json.loads(response.read())["data"]

    return LATEST_VERSIONS


def handler(event, context):
    """
    Respond with `307 - Temporary redirect`
    And redirect to latest version of dataset.
    If there is no such version, respond with `404 - Not Found`.
    """

    request = event["Records"][0]["cf"]["request"]
    host = event["Records"][0]["cf"]["config"]["distributionDomainName"]

    origin = request["headers"].get("origin", None)
    headers = {}

    # add access control allow origin header
    # in case an origin was included in request header to avoid cors issues
    if origin:
        headers["access-control-allow-origin"] = [
            {"key": "Access-Control-Allow-Origin", "value": "*"}
        ]
        headers["access-control-allow-methods"] = [
            {"key": "Access-Control-Allow-Methods", "value": "GET, HEAD"}
        ]

    path_items = request["uri"].split("/")
    query_string = request["querystring"]

    dataset = path_items[1]
    if dataset == "cog":
        query_params = parse_qs(query_string)
        dataset = query_params.get("dataset", ["cog"])[0]
        version = query_params.get("version", [None])[0]
    else:
        version = path_items[2]

    latest_versions = get_latest_versions(f"https://{host}/_latest")

    for latest_version in latest_versions:
        if latest_version["dataset"] == dataset or dataset == "cog":

            if "cog" in path_items:
                if version != "latest":
                    return request

                query_string = query_string.replace("latest", latest_version["version"])

            redirect_path = request["uri"].replace("latest", latest_version["version"])
            if query_string:
                redirect_path += f"?{query_string}"

            # set redirect path in location header
            headers["location"] = [{"key": "Location", "value": redirect_path}]

            response = {
                "status": "307",
                "statusDescription": "Temporary Redirect",
                "headers": headers,
            }

            return response

    # print(f"No `latest` version found for dataset {dataset}")

    response = {
        "status": "404",
        "statusDescription": "Not Found",
        "headers": headers,
        "body": json.dumps(
            {
                "status": "failed",
                "message": f"There is no `latest` version for dataset {dataset}",
            }
        ),
    }
    return response
