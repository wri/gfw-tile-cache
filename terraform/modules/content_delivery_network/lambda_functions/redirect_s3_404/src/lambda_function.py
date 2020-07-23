# mypy: ignore-errors


def handler(event, context):
    """
    This function updates the HTTP status code in the response to 307, to redirect to another
    path (cache behavior) that has a different origin configured. Note the following:
    1. The function is triggered in an origin response
    2. The response status from the origin server is an error status code (404)
    """

    response = event["Records"][0]["cf"]["response"]
    request = event["Records"][0]["cf"]["request"]
    headers = response["headers"]

    # if S3 returns a 404 sets custom origin properties
    # custom origin is tile cache app. URL is passed via custom header set in cloud front
    # (env variables are not support for Lambda@Edge)
    if int(response["status"]) == 404 and "default" in request["uri"]:

        redirect_path = request["uri"].replace("default", "dynamic")
        if request["querystring"]:
            redirect_path += f"?{request['querystring']}"

        headers["location"] = [{"key": "Location", "value": redirect_path}]
        headers["content-type"] = [{"key": "Content-Type", "value": "application/json"}]
        headers["content-encoding"] = [{"key": "Content-Encoding", "value": "UTF-8"}]

        response = {
            "status": "307",
            "statusDescription": "Temporary Redirect",
            "headers": headers,
        }

    return response
