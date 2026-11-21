import factory
from faker import Faker

from app.models import Comment, Post, User
from app.security import hash_password

fake = Faker()


class UserFactory(factory.Factory):
    class Meta:
        model = User

    email = factory.LazyFunction(fake.unique.safe_email)
    hashed_password = factory.LazyFunction(lambda: hash_password("factory-password"))


class PostFactory(factory.Factory):
    class Meta:
        model = Post

    title = factory.Faker("sentence", nb_words=6)
    content = factory.Faker("paragraph", nb_sentences=5)
    author = factory.SubFactory(UserFactory)


class CommentFactory(factory.Factory):
    class Meta:
        model = Comment

    content = factory.Faker("sentence")
    author = factory.SubFactory(UserFactory)
    post = factory.SubFactory(PostFactory)