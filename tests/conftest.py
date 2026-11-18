import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import Session, sessionmaker


def _database_identity(url: URL) -> tuple[str, str | None, int | None, str | None]:
    return url.drivername, url.host, url.port, url.database


def _get_test_database_url() -> URL:
    raw_test_url = os.getenv("TEST_DATABASE_URL")
    if not raw_test_url:
        raise RuntimeError("TEST_DATABASE_URL must be set before running tests")

    test_url = make_url(raw_test_url)
    if test_url.database != "blog_test":
        raise RuntimeError("Tests may only use the blog_test database")
    if test_url.username != "blog_test":
        raise RuntimeError("Tests must connect with the blog_test database role")

    for protected_name in ("DATABASE_URL", "PRODUCTION_DATABASE_URL"):
        raw_protected_url = os.getenv(protected_name)
        if raw_protected_url and _database_identity(test_url) == _database_identity(
            make_url(raw_protected_url)
        ):
            raise RuntimeError(
                f"TEST_DATABASE_URL must not point to the {protected_name} database"
            )
    return test_url


TEST_DATABASE_URL = _get_test_database_url()
test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)

from app.database import Base  # noqa: E402
from app import models  # noqa: E402,F401
from app.dependencies import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def create_test_schema() -> Generator[None, None, None]:
    Base.metadata.create_all(test_engine)
    yield
    Base.metadata.drop_all(test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    connection = test_engine.connect()
    transaction = connection.begin()
    test_session_factory = sessionmaker(
        bind=connection,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    session = test_session_factory()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
