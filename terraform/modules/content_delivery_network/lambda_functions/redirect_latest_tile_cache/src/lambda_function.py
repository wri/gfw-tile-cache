# mypy: ignore-errors

import json
import urllib.request

LATEST_VERSIONS = None


def get_latest_versions(url):
    """
    Get latest version for all datasets in Data API
    Use in memory object if exists, otherwise fetch from API
    B/C this is a Lambd@Edge function I cannot connect to a database inside VPC
    I also cannot read from S3, b/c I cannot set ENV variable to indicate the environment I am in
    Nor can I add a custom header to pass in variables b/c this is a viewer-request event-type
    The only option I have is to fetch the request URI and use it for my purposes
    """
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
    # print("REQUEST URI:" + request["uri"])

    path_items = request["uri"].split("/")
    dataset = path_items[1]

    # print("DATASET: " + dataset)

    latest_versions = get_latest_versions(f"https://{host}/_latest")

    for latest_version in latest_versions:
        if latest_version["dataset"] == dataset:
            # print("LATEST VERSION: " + latest_version["version"])
            path_items[2] = latest_version["version"]

            redirect_path = request["uri"].replace("latest", latest_version["version"])
            if request["querystring"]:
                redirect_path += f"?{request['querystring']}"

            # set redirect path in location header
            headers = {"location": [{"key": "Location", "value": redirect_path}]}

            # add access control allow origin header
            # in case an origin was included in request header to avoid cors issues
            origin = request["headers"].get("origin", None)
            if origin:
                headers["access-control-allow-origin"] = "*"

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
        "body": {"message": f"There is no `latest` version for dataset {dataset}"},
    }
    return response
