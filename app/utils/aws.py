import boto3
import httpx
from httpx_auth import AWS4Auth

from app.settings.globals import AWS_REGION, AWS_ENDPOINT_URI


async def invoke_lambda(function_name, payload, timeout=30):
    session = boto3.Session()
    cred = session.get_credentials()

    aws = AWS4Auth(
        access_id=cred.access_key,
        secret_key=cred.secret_key,
        security_token=cred.token,
        region=AWS_REGION,
        service="lambda",
    )

    lambda_host = AWS_ENDPOINT_URI if AWS_ENDPOINT_URI else f"https://lambda.{AWS_REGION}.amazonaws.com"
    print(f"LAMBDA HOST: {lambda_host}")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{lambda_host}/2015-03-31/functions/{function_name}/invocations",
            json=payload,
            auth=aws,
            timeout=timeout,
        )

    return response
