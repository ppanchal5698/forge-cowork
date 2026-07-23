from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All endpoints come from env (CLAUDE.md §3). aws_endpoint_url unset = real AWS."""

    aws_region: str = "us-east-1"
    aws_endpoint_url: str | None = None
    database_url: str = "postgresql://forge:forge@localhost:5432/forge"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "forgelocal"
    ollama_base_url: str = "http://localhost:11434"
    redis_url: str = "redis://localhost:6379/0"


settings = Settings()
