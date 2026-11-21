from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, event, inspect, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import Base
from app.models import Comment, Hamster, Post, User
from scripts.reset_db import reset_database


@pytest.fixture
def populated_engine() -> Iterator[Engine]:
    engine = create_engine("sqlite://")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, connection_record) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32))"))
        connection.execute(text("INSERT INTO alembic_version VALUES ('test_revision')"))
    with Session(engine) as session:
        user = User(email="user@example.com", hashed_password="hash")
        post = Post(title="Title", content="Content", author=user)
        session.add_all(
            [
                user,
                Comment(content="Comment", author=user, post=post),
                Hamster(name="Hamster", age=1, color="brown", user=user),
            ]
        )
        session.commit()
    yield engine
    engine.dispose()


def test_reset_deletes_rows_without_dropping_tables(
    populated_engine: Engine, capsys: pytest.CaptureFixture[str]
) -> None:
    reset_database(populated_engine)

    assert capsys.readouterr().out == (
        "Database reset succeeded: application table contents deleted.\n"
    )
    assert set(inspect(populated_engine).get_table_names()) == (
        set(Base.metadata.tables) | {"alembic_version"}
    )
    with Session(populated_engine) as session:
        for model in (User, Post, Comment, Hamster):
            assert session.scalars(select(model)).all() == []
        assert session.execute(text("SELECT version_num FROM alembic_version")).scalar() == (
            "test_revision"
        )


def test_reset_reports_failure_and_rolls_back(
    populated_engine: Engine, capsys: pytest.CaptureFixture[str]
) -> None:
    with populated_engine.begin() as connection:
        connection.execute(
            text(
                "CREATE TRIGGER prevent_user_delete BEFORE DELETE ON users "
                "BEGIN SELECT RAISE(ABORT, 'delete blocked'); END"
            )
        )

    with pytest.raises(SQLAlchemyError):
        reset_database(populated_engine)

    output = capsys.readouterr()
    assert output.out == ""
    assert "Database reset failed" in output.err
    with Session(populated_engine) as session:
        for model in (User, Post, Comment, Hamster):
            assert len(session.scalars(select(model)).all()) == 1
