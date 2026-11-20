import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app import seed
from app.database import Base
from app.models import User
from app.security import verify_password


def test_seed_persists_users_with_hashed_passwords(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    monkeypatch.setattr(seed, "SessionLocal", session_factory)

    seed.seed(seed.users)

    with session_factory() as session:
        users = {user.email: user for user in session.scalars(select(User)).all()}
        assert set(users) == {"admin@example.com", "demo@example.com"}
        assert verify_password(
            "admin-password", users["admin@example.com"].hashed_password
        )
        assert verify_password(
            "demo-password", users["demo@example.com"].hashed_password
        )
    engine.dispose()
