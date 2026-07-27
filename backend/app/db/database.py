from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a database session and always
    closes it, even if the request raised."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables registered on Base.metadata.

    Models must already be imported (directly or transitively) before
    this is called, otherwise their tables will not be registered.
    This is intentionally not called automatically on app startup so
    that a missing/unreachable database does not break the API from
    booting; run it explicitly (see verification steps).
    """
    Base.metadata.create_all(bind=engine)
