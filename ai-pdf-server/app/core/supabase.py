"""
Supabase client singleton for database operations in PDF Service.
"""

from typing import Optional
from supabase import create_client, Client

from app.core.config import settings
from app.utils.helpers import get_logger

logger = get_logger(__name__)


class SupabaseClient:
    """
    Singleton wrapper for Supabase client.
    
    Provides service (admin) client for database operations.
    """
    
    _instance: Optional["SupabaseClient"] = None
    _service_client: Optional[Client] = None
    
    def __new__(cls) -> "SupabaseClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Supabase client."""
        if self._service_client is None:
            self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Create Supabase client instance."""
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
            logger.warning("Supabase credentials not configured - persistence disabled")
            return
        
        try:
            self._service_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_KEY
            )
            logger.info("Supabase service client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    @property
    def client(self) -> Optional[Client]:
        """Get the service (admin) Supabase client."""
        return self._service_client
    
    def is_available(self) -> bool:
        """Check if Supabase client is available."""
        return self._service_client is not None
    
    def table(self, name: str):
        """Get a table reference."""
        if not self.is_available():
            raise RuntimeError("Supabase client not initialized")
        return self._service_client.table(name)


# Singleton instance
supabase = SupabaseClient()


def get_supabase() -> SupabaseClient:
    """Dependency injection helper for Supabase client."""
    return supabase
