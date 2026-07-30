"""Database engine and session configuration."""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.models import Base


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATABASE_DIRECTORY = PROJECT_ROOT / "database"
DATABASE_PATH = DATABASE_DIRECTORY / "strava_analytics.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def initialize_database() -> None:
    """Create the database directory and all registered tables."""

    DATABASE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_database_session() -> Generator[Session, None, None]:
    """Provide a database session and ensure it is closed afterward."""

    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()