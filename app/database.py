from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from app.config import settings

# DeclarativeBase: parent class for your table models
class Base(DeclarativeBase):
    pass

# engine is the connection to the database
# The settings object from config.py, which holds the DATABASE_URL from .env
engine = create_engine(settings.database_url, pool_pre_ping=True)

# Session: the object you use to talk to the database (query, add, commit)
# sessionmaker: a factory that creates new Session objects
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

# Generator is a type hint for functions that use "yield"
def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
