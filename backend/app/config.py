from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Creator Outreach Platform"
    debug: bool = False

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/creator_outreach"
    redis_url: str = "redis://localhost:6379"

    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60 * 24 * 7  # 1 week

    gemini_api_key: str = ""
    apollo_api_key: str = ""

    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_refresh_token: str = ""

    allowed_origins: list[str] = ["http://localhost:5173"]

    upload_dir: str = "./uploads"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
