def lambda_handler(event, context):
    """Add a response header to keep the response in cache for 1 year"""
    response = event["Records"][0]["cf"]["response"]
    response["headers"]["cache-control"] = "max-age=31536000"

    return response
