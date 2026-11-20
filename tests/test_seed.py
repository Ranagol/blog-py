import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app import seed
from app.database import Base
from app.models import User
from app.security import verify_password


def test_seed_persists_users_with_hashed_passwords(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    monkeypatch.setattr(seed, "SessionLocal", session_factory)

    seed.seed(seed.users)

    assert capsys.readouterr().out == (
        "Seeding succeeded: 2 users, 4 posts, and 8 comments added.\n"
    )
    with session_factory() as session:
        users = {user.email: user for user in session.scalars(select(User)).all()}
        assert set(users) == {"admin@example.com", "demo@example.com"}
        for user in users.values():
            assert len(user.posts) == 2
            for post in user.posts:
                assert len(post.comments) == 2
                assert post.author_id == user.id
                assert all(comment.author_id == user.id for comment in post.comments)
        assert verify_password(
            "admin-password", users["admin@example.com"].hashed_password
        )
        assert verify_password(
            "demo-password", users["demo@example.com"].hashed_password
        )
    engine.dispose()


def test_seed_reports_failure_and_rolls_back(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    monkeypatch.setattr(seed, "SessionLocal", session_factory)
    users = [
        User(email="duplicate@example.com", hashed_password="hash"),
        User(email="duplicate@example.com", hashed_password="hash"),
    ]

    with pytest.raises(IntegrityError):
        seed.seed(users)

    output = capsys.readouterr()
    assert output.out == ""
    assert "Seeding failed" in output.err
    with session_factory() as session:
        assert session.scalars(select(User)).all() == []
    engine.dispose()
