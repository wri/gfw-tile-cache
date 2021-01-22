import boto3
import httpx
from httpx_auth import AWS4Auth

from app.settings.globals import AWS_REGION, LAMBDA_HOST


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

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{LAMBDA_HOST}/2015-03-31/functions/{function_name}/invocations",
            json=payload,
            auth=aws,
            timeout=timeout,
        )

    return response
