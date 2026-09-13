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

    Models are imported here to ensure they are registered on Base.metadata.
    Also executes safe additive column migrations if running on PostgreSQL.
    """
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    try:
        if engine.dialect.name == "postgresql":
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE complaints ADD COLUMN IF NOT EXISTS quantity_unit VARCHAR;"))
                conn.execute(text("ALTER TABLE risk_assessments ADD COLUMN IF NOT EXISTS confidence_factors JSON;"))
                conn.commit()
    except Exception:
        pass
