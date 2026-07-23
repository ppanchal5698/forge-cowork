"""Package each skill (handler.py + shared/) into a zip and deploy it as a Lambda
to the configured endpoint. Idempotent: creates or updates.

MiniStack local dev deploy — production skill provisioning is Terraform in Sprint 4.
Run: docker compose cp ./skills backend:/skills && docker compose exec backend python /skills/deploy_skills.py
"""
import io
import os
import zipfile

import boto3

ENDPOINT = os.environ.get("AWS_ENDPOINT_URL")
REGION = os.environ.get("AWS_REGION", "us-east-1")
HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = ["summarize", "research"]


def zip_skill(name: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(os.path.join(HERE, name, "handler.py"), "handler.py")
        shared = os.path.join(HERE, "shared")
        for f in os.listdir(shared):
            if f.endswith(".py"):
                z.write(os.path.join(shared, f), f"shared/{f}")
    return buf.getvalue()


def ensure_role() -> str:
    iam = boto3.client("iam", region_name=REGION, endpoint_url=ENDPOINT)
    try:
        return iam.create_role(
            RoleName="forge-skill",
            AssumeRolePolicyDocument='{"Version":"2012-10-17","Statement":[]}',
        )["Role"]["Arn"]
    except iam.exceptions.EntityAlreadyExistsException:
        return iam.get_role(RoleName="forge-skill")["Role"]["Arn"]


def deploy(name: str, role_arn: str):
    lam = boto3.client("lambda", region_name=REGION, endpoint_url=ENDPOINT)
    code = zip_skill(name)
    fn = f"skill-{name}"
    env = {
        "Variables": {
            "OLLAMA_BASE_URL": os.environ["OLLAMA_BASE_URL"],
            "OLLAMA_MODEL": os.environ.get("OLLAMA_MODEL", "llama3.2:1b"),
        }
    }
    try:
        lam.create_function(
            FunctionName=fn,
            Runtime="python3.12",
            Role=role_arn,
            Handler="handler.handler",
            Code={"ZipFile": code},
            Environment=env,
            Timeout=180,
        )
        print(f"created {fn}")
    except lam.exceptions.ResourceConflictException:
        lam.update_function_code(FunctionName=fn, ZipFile=code)
        lam.update_function_configuration(FunctionName=fn, Environment=env)
        print(f"updated {fn}")


if __name__ == "__main__":
    role = ensure_role()
    for skill in SKILLS:
        deploy(skill, role)
    print("skills deployed")
