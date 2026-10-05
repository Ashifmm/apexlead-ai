import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Configuration loaded from environment variables and .env file.
    """
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "AI Web Agency Lead Generation System"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Server Binding
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite:///./agency_leads.db"

    # Google Gemini API
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Instagram Automation Credentials
    INSTAGRAM_USERNAME: str = ""
    INSTAGRAM_USER_ID: str = ""
    INSTAGRAM_SESSION_ID: str = ""
    INSTAGRAM_DAILY_LIMIT: int = 15

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_gemini_configured(self) -> bool:
        return bool(self.GEMINI_API_KEY and self.GEMINI_API_KEY.strip() != "")

    @property
    def is_instagram_configured(self) -> bool:
        return bool(self.INSTAGRAM_SESSION_ID and self.INSTAGRAM_SESSION_ID.strip() != "")


settings = Settings()
