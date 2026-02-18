"""
Supabase client singleton for database and auth operations.
"""

from typing import Optional
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

from app.core.config import settings
from app.utils.helpers import get_logger

logger = get_logger(__name__)


class SupabaseClient:
    """
    Singleton wrapper for Supabase client.
    
    Provides both anon (public) and service (admin) clients:
    - anon_client: For user-facing operations (respects RLS)
    - service_client: For admin operations (bypasses RLS)
    """
    
    _instance: Optional["SupabaseClient"] = None
    _anon_client: Optional[Client] = None
    _service_client: Optional[Client] = None
    
    def __new__(cls) -> "SupabaseClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Supabase clients."""
        if self._anon_client is None:
            self._initialize_clients()
    
    def _initialize_clients(self) -> None:
        """Create Supabase client instances."""
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            logger.warning("Supabase credentials not configured")
            return
        
        try:
            # Anon client for user operations
            self._anon_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY
            )
            logger.info("Supabase anon client initialized")
            
            # Service client for admin operations (if key provided)
            if settings.SUPABASE_SERVICE_KEY:
                self._service_client = create_client(
                    settings.SUPABASE_URL,
                    settings.SUPABASE_SERVICE_KEY
                )
                logger.info("Supabase service client initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase clients: {e}")
            raise
    
    @property
    def client(self) -> Client:
        """Get the anon (public) Supabase client."""
        if self._anon_client is None:
            raise RuntimeError("Supabase client not initialized")
        return self._anon_client
    
    @property
    def admin(self) -> Client:
        """Get the service (admin) Supabase client."""
        if self._service_client is None:
            if self._anon_client is None:
                raise RuntimeError("Supabase client not initialized")
            # Fall back to anon client if no service key
            logger.warning("Using anon client as admin (no service key)")
            return self._anon_client
        return self._service_client
    
    @property
    def auth(self):
        """Get the auth client for authentication operations."""
        return self.client.auth
    
    @property
    def auth_admin(self):
        """Get the admin auth client for admin operations."""
        return self.admin.auth.admin
    
    def table(self, name: str):
        """Get a table reference (uses anon client)."""
        return self.client.table(name)
    
    def admin_table(self, name: str):
        """Get a table reference (uses service client, bypasses RLS)."""
        return self.admin.table(name)
    
    async def health_check(self) -> dict:
        """Check Supabase connection health."""
        try:
            # Try to fetch from a simple query
            result = self.client.table("profiles").select("id").limit(1).execute()
            return {
                "status": "healthy",
                "supabase_url": settings.SUPABASE_URL,
                "has_service_key": bool(settings.SUPABASE_SERVICE_KEY)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Singleton instance
supabase = SupabaseClient()


def get_supabase() -> SupabaseClient:
    """Dependency injection helper for Supabase client."""
    return supabase
