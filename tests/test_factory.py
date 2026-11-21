from email_validator import validate_email

from app.factory import CommentFactory, PostFactory, UserFactory
from app.models import Comment, Post, User
from app.schemas.comments import CommentCreate
from app.schemas.posts import PostCreate


def test_factories_build_related_models() -> None:
    user = UserFactory()
    post = PostFactory(author=user)
    comment = CommentFactory(author=user, post=post)

    assert isinstance(user, User)
    assert isinstance(post, Post)
    assert isinstance(comment, Comment)
    assert post.author is user
    assert comment.author is user
    assert comment.post is post
    assert post in user.posts
    assert comment in post.comments


def test_factories_generate_valid_unique_emails_and_text() -> None:
    users = UserFactory.build_batch(10)
    emails = [user.email for user in users]
    assert len(set(emails)) == len(emails)
    for email in emails:
        assert validate_email(email, check_deliverability=False).normalized == email

    post = PostFactory.build(author=users[0])
    comment = CommentFactory.build(author=users[1], post=post)
    assert PostCreate(title=post.title, content=post.content)
    assert CommentCreate(content=comment.content)
