"""
Gateway configuration.
"""

import os
from typing import List
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Gateway settings from environment variables."""
    
    # App settings
    APP_NAME: str = os.getenv("APP_NAME", "API Gateway")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8080"))
    
    # Backend service URLs
    PDF_SERVICE_URL: str = os.getenv("PDF_SERVICE_URL", "http://localhost:8000")
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://localhost:8001")
    
    # JWT settings (for validating tokens from User-Service)
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        origin.strip() 
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    ]
    
    # Timeouts (seconds)
    REQUEST_TIMEOUT: float = float(os.getenv("REQUEST_TIMEOUT", "60"))
    CONNECT_TIMEOUT: float = float(os.getenv("CONNECT_TIMEOUT", "10"))
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
