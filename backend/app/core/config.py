from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Bot Licensing Server"
    app_version: str = "0.1.0"
    database_url: str = "postgresql+psycopg://bot_licensing:bot_licensing@postgres:5432/bot_licensing"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
