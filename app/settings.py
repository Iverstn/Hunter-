from datetime import date

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_env: str = "development"
    base_url: str = "http://localhost:8000"
    dashboard_password: str = "changeme"
    default_email_recipient: str = "jasonlinpng@gmail.com"
    timezone: str = "Asia/Singapore"

    x_api_bearer_token: str | None = None
    x_scrape_fallback: bool = False
    youtube_api_key: str | None = None
    google_cse_api_key: str | None = None
    google_cse_cx: str | None = None

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_sender: str | None = None

    session_secret: str = "dev-secret"
    data_dir: str = "data"
    content_min_date: date = date(2025, 11, 1)
    content_max_age_days: int = 7


settings = Settings()
