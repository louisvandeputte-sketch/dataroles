from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""
    
    # Supabase
    supabase_url: str
    supabase_key: str
    
    # Bright Data
    brightdata_api_token: str
    brightdata_dataset_id: str = "gd_lpfll7v5hcqtkxl6l"  # LinkedIn dataset
    # Indeed dataset ID is hardcoded in client: gd_l4dx9j9sscpvs7no2
    brightdata_max_concurrent_requests: int = 3
    brightdata_poll_interval: int = 30
    brightdata_timeout: int = 1800
    brightdata_daily_quota: int = 10000
    
    # OpenAI
    openai_api_key: Optional[str] = None
    
    # Application
    environment: str = "development"
    use_mock_api: bool = False
    log_level: str = "INFO"
    
    # Web Server
    web_host: str = "0.0.0.0"
    web_port: int = 8000
    web_admin_username: str = "admin"
    web_admin_password: str = "changeme"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

# Global settings instance
settings = Settings()
