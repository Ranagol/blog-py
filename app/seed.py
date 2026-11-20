from app.database import SessionLocal
from app.models import User
from app.security import hash_password

users = [
    User(email="admin@example.com", hashed_password=hash_password("admin-password")),
    User(email="demo@example.com", hashed_password=hash_password("demo-password"))
]

# Run it with 
# python3 -m app.seed
# We define the seeding function here
def seed(users: list[User]):

    db = SessionLocal()
    try:
        db.add_all(users)
        db.commit()
    finally:
        db.close()

# We run the seeding function here. But, we do not want to run this seeder every time, when this
# file is loaded. Example, it could be loaded during testing. We want to trigger seed() only, when
# triggered by python -m app.seed command. If it was started from root, by terminal command, the
# __name__ will be "__main__" only when this file is executed directly. If the seed.py was imported
# as a module from a random .py file, then the name will not be "__main__".
if __name__ == "__main__":
    seed(users)