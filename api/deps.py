"""
Shared dependencies for API routes.
"""

from database.db_manager import DatabaseManager

# Global database manager (set by lifespan in api.main)
_db_manager: DatabaseManager | None = None


def get_db_manager() -> DatabaseManager:
    """Get the active database manager. Used as a FastAPI dependency."""
    if _db_manager is None:
        raise RuntimeError("Database not initialized")
    return _db_manager


def set_db_manager(manager: DatabaseManager) -> None:
    """Set the global database manager (called from lifespan)."""
    global _db_manager
    _db_manager = manager


def clear_db_manager() -> None:
    """Clear the global database manager (called from shutdown)."""
    global _db_manager
    _db_manager = None
