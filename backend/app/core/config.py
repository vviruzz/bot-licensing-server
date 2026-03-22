from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Bot Licensing Server"
    app_version: str = "0.1.0"
    database_url: str = "postgresql+psycopg://bot_licensing:bot_licensing@postgres:5432/bot_licensing"

    admin_jwt_secret: str = "change-me-admin-jwt-secret"
    admin_jwt_algorithm: str = "HS256"
    admin_jwt_expire_minutes: int = 60

    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None
    bootstrap_admin_role: str = "owner"
    bootstrap_admin_name: str = "Bootstrap Admin"

    bot_api_token: str = "change-me-bot-token"
    bot_request_max_age_seconds: int = 300
    bot_request_max_future_skew_seconds: int = 30
    bot_endpoint_rate_limit: int = 120
    bot_endpoint_rate_window_seconds: int = 60
    admin_login_rate_limit: int = 5
    admin_login_rate_window_seconds: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
