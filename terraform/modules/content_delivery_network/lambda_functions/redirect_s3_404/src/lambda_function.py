import logging


def handler(event, context):
    print(event["Records"][0]["cf"])

    response = event["Records"][0]["cf"]["response"]
    request = event["Records"][0]["cf"]["request"]

    # if S3 returns a 404 sets custom origin properties
    # custom origin is tile cache app. URL is passed via custom header set in cloud front
    # (env variables are not support for Lambda@Edge)

    print("Check response status")
    """
    This function updates the HTTP status code in the response to 302, to redirect to another
    path (cache behavior) that has a different origin configured. Note the following:
    1. The function is triggered in an origin response
    2. The response status from the origin server is an error status code (404)
    """

    if int(response["status"]) == 404 and "default" in request["uri"]:
        redirect_path = request["uri"].replace("default", "dynamic")

        response["status"] = 302
        response["statusDescription"] = "Found"

        # Drop the body as it is not required for redirects
        response["body"] = ""
        response["headers"]["location"] = [{"key": "Location", "value": redirect_path}]

    return response
