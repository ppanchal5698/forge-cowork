from .aws import client
from .config import settings


def artifact_key(tenant_id: str, run_id: str, name: str) -> str:
    """Tenant-prefixed S3 key. Empty tenant/run is rejected — CLAUDE.md §5 forbids
    bucket-root or un-tenanted paths, and that rule lives in this one function."""
    if not tenant_id or not run_id:
        raise ValueError("tenant_id and run_id are required for artifact keys")
    return f"artifacts/{tenant_id}/{run_id}/{name}"


def put_artifact(
    tenant_id: str,
    run_id: str,
    name: str,
    body: bytes,
    content_type: str = "application/octet-stream",
) -> str:
    key = artifact_key(tenant_id, run_id, name)
    client("s3").put_object(
        Bucket=settings.artifacts_bucket, Key=key, Body=body, ContentType=content_type
    )
    return key


def get_artifact(key: str) -> bytes:
    return client("s3").get_object(Bucket=settings.artifacts_bucket, Key=key)["Body"].read()
