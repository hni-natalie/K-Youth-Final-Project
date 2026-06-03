import sqlite3
from contextlib import contextmanager
from backend.core.config import settings

@contextmanager
def get_db():
    """Context manager for SQLite connection."""
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()