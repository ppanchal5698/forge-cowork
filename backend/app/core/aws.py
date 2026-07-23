import boto3

from .config import settings


def client(service: str):
    """Single factory for all AWS clients — endpoint from config, never hardcoded."""
    return boto3.client(
        service,
        region_name=settings.aws_region,
        endpoint_url=settings.aws_endpoint_url,
    )
