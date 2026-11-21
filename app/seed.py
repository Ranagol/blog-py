import random
import sys

from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.database import SessionLocal
from app.factory import CommentFactory, PostFactory, UserFactory
from app.security import hash_password

USER_COUNT = 10
POSTS_PER_USER = 2
COMMENTS_PER_POST = 2

DEFAULT_USER_EMAIL = settings.default_user_email
DEFAULT_USER_PASSWORD = settings.default_user_password

def seed() -> None:
    try:
        # Create the default user
        default_user = UserFactory.build(
            email=DEFAULT_USER_EMAIL,
            hashed_password=hash_password(DEFAULT_USER_PASSWORD.get_secret_value()),
        )
        users = [default_user]

        # Create 10 users
        users += UserFactory.build_batch(USER_COUNT)
        for user in users:
            for _ in range(POSTS_PER_USER):
                # Create 2 posts for each user
                post = PostFactory.build(author=user)
                for _ in range(COMMENTS_PER_POST):
                    # Create 2 comments for each post, from random existing users
                    CommentFactory.build(post=post, author=random.choice(users))

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
    seed()

