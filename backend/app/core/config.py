from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    storage_dir: str = "storage"
    max_upload_mb: int = 50
    file_ttl_minutes: int = 30
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
