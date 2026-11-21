import pytest
from pydantic import SecretStr
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app import seed
from app.database import Base
from app.models import Comment, Post, User
from app.security import verify_password


def test_seed_persists_factory_users_posts_and_comments(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    monkeypatch.setattr(seed, "SessionLocal", session_factory)
    monkeypatch.setattr(seed, "DEFAULT_USER_EMAIL", "configured@example.com")
    monkeypatch.setattr(seed, "DEFAULT_USER_PASSWORD", SecretStr("configured-password"))
    chosen_emails = []

    def choose_last(users: list[User]) -> User:
        chosen_emails.append(users[-1].email)
        return users[-1]

    monkeypatch.setattr(seed.random, "choice", choose_last)
    seed.seed()

    assert capsys.readouterr().out == (
        "Seeding succeeded: 11 users, 22 posts, and 44 comments added.\n"
    )
    with session_factory() as session:
        users = session.scalars(select(User)).all()
        posts = session.scalars(select(Post)).all()
        comments = session.scalars(select(Comment)).all()
        assert len(users) == 11
        assert len(posts) == 22
        assert len(comments) == 44
        user_ids = {user.id for user in users}
        assert len(chosen_emails) == 44
        chosen_id = next(user.id for user in users if user.email == chosen_emails[0])
        assert all(comment.author_id == chosen_id for comment in comments)
        assert all(comment.author_id in user_ids for comment in comments)
        for user in users:
            password = (
                "configured-password"
                if user.email == "configured@example.com"
                else "factory-password"
            )
            assert verify_password(password, user.hashed_password)
            assert len(user.posts) == 2
            for post in user.posts:
                assert len(post.comments) == 2
                assert post.author_id == user.id
        assert sum(user.email == "configured@example.com" for user in users) == 1
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
    monkeypatch.setattr(seed.UserFactory, "build_batch", lambda size: users)

    with pytest.raises(IntegrityError):
        seed.seed()

    output = capsys.readouterr()
    assert output.out == ""
    assert "Seeding failed" in output.err
    with session_factory() as session:
        assert session.scalars(select(User)).all() == []
        assert session.scalars(select(Post)).all() == []
        assert session.scalars(select(Comment)).all() == []
    engine.dispose()
