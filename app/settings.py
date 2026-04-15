from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Evidence Gap Coach"
    database_url: str = "sqlite:///./evidence_gap.db"
    recent_window_days: int = 180
    pending_review_lag_days: int = 14
    ask_threshold: float = 0.55

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
