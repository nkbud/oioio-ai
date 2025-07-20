"""
Database configuration and base models.
"""
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import Column, MetaData, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from oioio_mcp_agent.config import Config

metadata = MetaData()
Base = declarative_base(metadata=metadata)

# Connection pool configuration
POOL_SIZE = 5
MAX_OVERFLOW = 10
POOL_RECYCLE = 3600  # Recycle connections after 1 hour


class DBConfig:
    """Database configuration class."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize database configuration."""
        self.config = config or Config.load()
        self.engine = None
        self.session_local = None

    def setup(self, db_url: Optional[str] = None) -> None:
        """Set up database connection."""
        if db_url is None:
            # Default to SQLite for local development
            db_url = self.config.get("api", {}).get(
                "database_url", "sqlite:///./oioio_mcp_agent.db"
            )

        connect_args = {}
        if db_url.startswith("sqlite"):
            connect_args = {"check_same_thread": False}

        self.engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=POOL_SIZE,
            max_overflow=MAX_OVERFLOW,
            pool_recycle=POOL_RECYCLE,
            connect_args=connect_args,
        )
        self.session_local = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_db_session(self):
        """Get database session."""
        if self.session_local is None:
            self.setup()

        db = self.session_local()
        try:
            yield db
        finally:
            db.close()


# Singleton instance
db_config = DBConfig()


# Helper function to get database session
def get_db():
    """Get database session."""
    return next(db_config.get_db_session())