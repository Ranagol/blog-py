from datetime import UTC, datetime, timedelta

import jwt
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.testclient import TestClient

from app.config import settings
from app.models import Comment, Post, User
from app.security import ALGORITHM


def register(
    client: TestClient,
    email: str = "reader@example.com",
    password: str = "correct-horse-battery",
) -> dict[str, object]:
    response = client.post(
        "/users/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201
    return response.json()


def authorization_header(
    client: TestClient,
    email: str = "reader@example.com",
    password: str = "correct-horse-battery",
) -> dict[str, str]:
    response = client.post(
        "/users/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_registration_normalizes_email_and_does_not_expose_hash(
    client: TestClient,
) -> None:
    response = client.post(
        "/users/register",
        json={"email": "  Reader@Example.com ", "password": "a-secure-password"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "reader@example.com"
    assert "hashed_password" not in body
    assert "password" not in body
    assert body["id"] > 0
    assert body["created_at"]


def test_registration_rejects_case_insensitive_duplicate(
    client: TestClient,
) -> None:
    register(client)

    response = client.post(
        "/users/register",
        json={"email": "READER@example.com", "password": "another-password"},
    )

    assert response.status_code == 409


@pytest.mark.parametrize("email", ["not-an-email", ""])
def test_registration_rejects_invalid_email(client: TestClient, email: str) -> None:
    response = client.post(
        "/users/register",
        json={"email": email, "password": "a-secure-password"},
    )
    assert response.status_code == 422


def test_login_issues_bearer_token(client: TestClient) -> None:
    user = register(client)

    response = client.post(
        "/users/login",
        json={"email": "READER@example.com", "password": "correct-horse-battery"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    decoded = jwt.decode(
        response.json()["access_token"],
        settings.secret_key.get_secret_value(),
        algorithms=[ALGORITHM],
    )
    assert decoded["sub"] == str(user["id"])
    assert decoded["exp"] > datetime.now(UTC).timestamp()


def test_login_uses_same_error_for_unknown_email_and_bad_password(
    client: TestClient,
) -> None:
    register(client)
    unknown = client.post(
        "/users/login",
        json={"email": "unknown@example.com", "password": "wrong-password"},
    )
    incorrect = client.post(
        "/users/login",
        json={"email": "reader@example.com", "password": "wrong-password"},
    )

    assert unknown.status_code == incorrect.status_code == 401
    assert unknown.json() == incorrect.json()


def test_protected_endpoint_rejects_missing_invalid_and_expired_tokens(
    client: TestClient,
) -> None:
    register(client)
    expired = jwt.encode(
        {
            "sub": "1",
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        settings.secret_key.get_secret_value(),
        algorithm=ALGORITHM,
    )
    invalid_subject = jwt.encode(
        {
            "sub": "not-a-user-id",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        settings.secret_key.get_secret_value(),
        algorithm=ALGORITHM,
    )

    for headers in (
        {},
        {"Authorization": "Bearer invalid"},
        {"Authorization": f"Bearer {expired}"},
        {"Authorization": f"Bearer {invalid_subject}"},
    ):
        response = client.post(
            "/posts",
            json={"title": "Title", "content": "Content"},
            headers=headers,
        )
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"


def test_posts_are_public_and_return_only_public_author_data(
    client: TestClient,
) -> None:
    user = register(client)
    headers = authorization_header(client)
    created = client.post(
        "/posts",
        json={"title": "  First post  ", "content": " Post body "},
        headers=headers,
    )
    assert created.status_code == 201
    assert created.json()["title"] == "First post"
    assert created.json()["content"] == " Post body "
    assert created.json()["author"] == {"id": user["id"]}
    assert "author_id" not in created.json()
    assert "email" not in created.json()["author"]

    listed = client.get("/posts")
    detail = client.get(f"/posts/{created.json()['id']}")

    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert detail.status_code == 200
    assert detail.json()["id"] == created.json()["id"]


def test_posts_and_comments_use_the_documented_order(
    client: TestClient,
    db_session: Session,
) -> None:
    user_data = register(client)
    user = db_session.get(User, user_data["id"])
    assert user is not None
    timestamp = datetime(2025, 1, 1, tzinfo=UTC)
    older_id_post = Post(
        title="First",
        content="First",
        created_at=timestamp,
        updated_at=timestamp,
        author_id=user.id,
    )
    newer_id_post = Post(
        title="Second",
        content="Second",
        created_at=timestamp,
        updated_at=timestamp,
        author_id=user.id,
    )
    db_session.add_all([older_id_post, newer_id_post])
    db_session.commit()
    first_comment = Comment(
        content="First",
        created_at=timestamp,
        updated_at=timestamp,
        author_id=user.id,
        post_id=older_id_post.id,
    )
    second_comment = Comment(
        content="Second",
        created_at=timestamp,
        updated_at=timestamp,
        author_id=user.id,
        post_id=older_id_post.id,
    )
    db_session.add_all([first_comment, second_comment])
    db_session.commit()

    posts = client.get("/posts").json()
    comments = client.get(f"/posts/{older_id_post.id}/comments").json()

    assert [post["id"] for post in posts] == [newer_id_post.id, older_id_post.id]
    assert [comment["id"] for comment in comments] == [
        first_comment.id,
        second_comment.id,
    ]


@pytest.mark.parametrize(
    ("title", "content"),
    [
        ("", "content"),
        ("  \t ", "content"),
        ("title", ""),
        ("title", " \n "),
    ],
)
def test_post_creation_rejects_blank_content(
    client: TestClient,
    title: str,
    content: str,
) -> None:
    register(client)
    response = client.post(
        "/posts",
        json={"title": title, "content": content},
        headers=authorization_header(client),
    )
    assert response.status_code == 422


def test_post_update_is_full_replacement_and_changes_updated_at(
    client: TestClient,
) -> None:
    register(client)
    headers = authorization_header(client)
    post = client.post(
        "/posts",
        json={"title": "Before", "content": "Before content"},
        headers=headers,
    ).json()

    incomplete = client.put(
        f"/posts/{post['id']}",
        json={"title": "After"},
        headers=headers,
    )
    updated = client.put(
        f"/posts/{post['id']}",
        json={"title": "After", "content": "After content"},
        headers=headers,
    )

    assert incomplete.status_code == 422
    assert updated.status_code == 200
    assert updated.json()["content"] == "After content"
    assert updated.json()["updated_at"] > post["updated_at"]


def test_users_cannot_update_or_delete_another_users_post(
    client: TestClient,
) -> None:
    register(client)
    owner_headers = authorization_header(client)
    post = client.post(
        "/posts",
        json={"title": "Owned", "content": "Post body"},
        headers=owner_headers,
    ).json()
    register(client, "other@example.com", "another-secure-password")
    other_headers = authorization_header(
        client, "other@example.com", "another-secure-password"
    )

    updated = client.put(
        f"/posts/{post['id']}",
        json={"title": "Changed", "content": "Changed"},
        headers=other_headers,
    )
    deleted = client.delete(f"/posts/{post['id']}", headers=other_headers)

    assert updated.status_code == 404
    assert deleted.status_code == 404
    assert client.get(f"/posts/{post['id']}").status_code == 200
    missing_update = client.put(
        "/posts/999999",
        json={"title": "Changed", "content": "Changed"},
        headers=owner_headers,
    )
    missing_delete = client.delete("/posts/999999", headers=owner_headers)
    assert missing_update.status_code == 404
    assert missing_delete.status_code == 404


def test_post_delete_removes_its_comments(
    client: TestClient,
    db_session: Session,
) -> None:
    register(client)
    headers = authorization_header(client)
    post = client.post(
        "/posts",
        json={"title": "Parent", "content": "Post body"},
        headers=headers,
    ).json()
    comment = client.post(
        f"/posts/{post['id']}/comments",
        json={"content": "Comment body"},
        headers=headers,
    ).json()

    response = client.delete(f"/posts/{post['id']}", headers=headers)

    assert response.status_code == 204
    assert response.content == b""
    assert db_session.scalar(
        select(Comment).where(Comment.id == comment["id"])
    ) is None


def test_comments_are_public_and_omits_author_email(client: TestClient) -> None:
    user = register(client)
    headers = authorization_header(client)
    post = client.post(
        "/posts",
        json={"title": "Post", "content": "Post body"},
        headers=headers,
    ).json()
    created = client.post(
        f"/posts/{post['id']}/comments",
        json={"content": "  Comment body  "},
        headers=headers,
    )

    assert created.status_code == 201
    assert created.json()["content"] == "  Comment body  "
    assert created.json()["author"] == {"id": user["id"]}
    assert "email" not in created.json()["author"]
    listed = client.get(f"/posts/{post['id']}/comments")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [created.json()["id"]]


def test_comment_creation_rejects_blank_content(client: TestClient) -> None:
    register(client)
    headers = authorization_header(client)
    post = client.post(
        "/posts",
        json={"title": "Post", "content": "Post body"},
        headers=headers,
    ).json()

    response = client.post(
        f"/posts/{post['id']}/comments",
        json={"content": " \t "},
        headers=headers,
    )

    assert response.status_code == 422


def test_comment_update_delete_and_ownership(client: TestClient) -> None:
    register(client)
    owner_headers = authorization_header(client)
    post = client.post(
        "/posts",
        json={"title": "Post", "content": "Post body"},
        headers=owner_headers,
    ).json()
    comment = client.post(
        f"/posts/{post['id']}/comments",
        json={"content": "Before"},
        headers=owner_headers,
    ).json()
    incomplete_update = client.put(
        f"/comments/{comment['id']}",
        json={},
        headers=owner_headers,
    )
    register(client, "other@example.com", "another-secure-password")
    other_headers = authorization_header(
        client, "other@example.com", "another-secure-password"
    )

    forbidden_update = client.put(
        f"/comments/{comment['id']}",
        json={"content": "Not yours"},
        headers=other_headers,
    )
    owner_update = client.put(
        f"/comments/{comment['id']}",
        json={"content": "After"},
        headers=owner_headers,
    )
    deleted = client.delete(
        f"/comments/{comment['id']}",
        headers=owner_headers,
    )

    assert forbidden_update.status_code == 404
    assert incomplete_update.status_code == 422
    assert owner_update.status_code == 200
    assert owner_update.json()["content"] == "After"
    assert owner_update.json()["updated_at"] > comment["updated_at"]
    assert deleted.status_code == 204
    assert deleted.content == b""


def test_missing_post_returns_404_for_comment_routes(client: TestClient) -> None:
    register(client)
    headers = authorization_header(client)

    listed = client.get("/posts/999999/comments")
    created = client.post(
        "/posts/999999/comments",
        json={"content": "Orphan"},
        headers=headers,
    )

    assert listed.status_code == 404
    assert created.status_code == 404
