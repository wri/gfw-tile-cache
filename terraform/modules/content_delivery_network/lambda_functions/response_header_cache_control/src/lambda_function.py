# mypy: ignore-errors


def handler(event, context):
    """Add a response header to keep the response in cache for 1 year"""
    response = event["Records"][0]["cf"]["response"]
    response["headers"]["cache-control"] = [
        {"key": "Cache-Control", "value": "max-age=31536000"}
    ]

    return response
