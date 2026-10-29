"""Database session and connection management."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path
from contextlib import contextmanager
from typing import Optional

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from src.attribution.db.models import Base

# Module-level cached engine
_DEFAULT_ENGINE: Optional[Engine] = None


def get_default_engine() -> Engine:
    """Return a shared singleton engine for the default database URL."""
    global _DEFAULT_ENGINE
    if _DEFAULT_ENGINE is None:
        _DEFAULT_ENGINE = create_db_engine()
    return _DEFAULT_ENGINE


@contextmanager
def get_db_session(engine: Optional[Engine] = None) -> Generator[Session, None, None]:
    """Yield a database session and safely commit or rollback."""
    eng = engine or get_default_engine()
    factory = get_session_factory(eng)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_default_database_url() -> str:
    """Retrieve database URL from environment or return default local SQLite path."""
    try:
        from dotenv import load_dotenv
        backend_root = Path(__file__).resolve().parent.parent.parent.parent
        env_file = backend_root / ".env"
        if env_file.is_file():
            load_dotenv(dotenv_path=env_file)
        else:
            load_dotenv()
    except Exception:
        pass

    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    
    # Default to local SQLite database in backend data directory
    backend_root = Path(__file__).resolve().parent.parent.parent.parent
    data_dir = backend_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "marketing_attribution.db"
    return f"sqlite:///{db_path.as_posix()}"


def create_db_engine(db_url: Optional[str] = None, echo: bool = False) -> Engine:
    """Create SQLAlchemy engine with appropriate dialect tuning."""
    url = db_url or get_default_database_url()
    
    # Enable SQLite specific pragmas
    if url.startswith("sqlite"):
        engine = create_engine(
            url,
            echo=echo,
            connect_args={"check_same_thread": False},
        )
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.close()
    else:
        # PostgreSQL / other production engines
        # If generic postgresql:// URL is used, adapt to whichever driver is installed
        if url.startswith("postgresql://"):
            try:
                import psycopg  # noqa: F401
            except ImportError:
                try:
                    import psycopg2  # noqa: F401
                    url = "postgresql+psycopg2://" + url[len("postgresql://"):]
                except ImportError:
                    pass

        engine = create_engine(
            url,
            echo=echo,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
    
    return engine


def init_db(engine: Engine) -> None:
    """Initialize database tables according to SQLAlchemy metadata."""
    Base.metadata.create_all(bind=engine)


def drop_db(engine: Engine) -> None:
    """Drop all tables according to SQLAlchemy metadata."""
    Base.metadata.drop_all(bind=engine)


def get_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Get a sessionmaker bound to the given engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session(engine: Engine) -> Generator[Session, None, None]:
    """Yield a database session and safely commit or rollback."""
    factory = get_session_factory(engine)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

