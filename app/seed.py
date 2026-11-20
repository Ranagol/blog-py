import sys

from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.models import Comment, Post, User
from app.security import hash_password

users = [
    User(email="admin@example.com", hashed_password=hash_password("admin-password")),
    User(email="demo@example.com", hashed_password=hash_password("demo-password")),
]

POSTS_PER_USER = 2
COMMENTS_PER_POST = 2


def seed(users: list[User]) -> None:
    for user in users:
        for post_number in range(1, POSTS_PER_USER + 1):
            user.posts.append(
                Post(
                    title=f"Seed post {post_number}",
                    content=f"Seed post {post_number} by {user.email}.",
                    comments=[
                        Comment(
                            content=f"Seed comment {comment_number} on post {post_number}.",
                            author=user,
                        )
                        for comment_number in range(1, COMMENTS_PER_POST + 1)
                    ],
                )
            )

    try:
        with SessionLocal() as db:
            db.add_all(users)
            db.commit()
    except SQLAlchemyError:
        print("Seeding failed. See the error details below.", file=sys.stderr)
        raise

    post_count = len(users) * POSTS_PER_USER
    comment_count = post_count * COMMENTS_PER_POST
    print(
        f"Seeding succeeded: {len(users)} users, {post_count} posts, "
        f"and {comment_count} comments added."
    )


# Run with: docker compose exec backend python -m app.seed
if __name__ == "__main__":
    seed(users)


