from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/sigma"
    json_logs: bool = False  # в проде — True: JSON в stdout для сбора логов


settings = Settings()
