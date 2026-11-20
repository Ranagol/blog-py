import sys

from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.models import User
from app.security import hash_password

users = [
    User(email="admin@example.com", hashed_password=hash_password("admin-password")),
    User(email="demo@example.com", hashed_password=hash_password("demo-password")),
]


def seed(users: list[User]) -> None:
    try:
        with SessionLocal() as db:
            db.add_all(users)
            db.commit()
    except SQLAlchemyError:
        print("Seeding failed. See the error details below.", file=sys.stderr)
        raise

    print(f"Seeding succeeded: {len(users)} users added.")


# Run with: docker compose exec backend python -m app.seed
if __name__ == "__main__":
    seed(users)
