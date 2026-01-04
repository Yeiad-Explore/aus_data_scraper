"""Configuration settings using Pydantic Settings."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # URLs (configurable via environment variables)
    BASE_URL: str = ""
    ENTRY_URL: str = ""

    # Delays (anti-blocking)
    MIN_DELAY_SECONDS: float = 3.0
    MAX_DELAY_SECONDS: float = 6.0

    # Timeouts (milliseconds)
    PAGE_LOAD_TIMEOUT: int = 30000
    NAVIGATION_TIMEOUT: int = 60000

    # Storage
    DATA_DIR: Path = Path("data")
    RAW_DIR: Path = Path("data/raw")
    PARSED_DIR: Path = Path("data/parsed")
    ENRICHED_DIR: Path = Path("data/enriched")
    STATE_DIR: Path = Path("data/state")
    LOGS_DIR: Path = Path("logs")

    # Browser
    HEADLESS: bool = True
    BROWSER_TYPE: str = "chromium"

    # LLM (optional)
    LLM_PROVIDER: str = "anthropic"  # "anthropic", "openai", or "azure"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "claude-3-5-sonnet-20241022"
    LLM_TEMPERATURE: float = 0.0

    # Azure OpenAI specific settings
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = ""

    # Retry
    MAX_RETRIES: int = 1

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Global settings instance
settings = Settings()
