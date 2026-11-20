from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.dependencies import CurrentUser, DbSession
from app.models import Comment, Post
from app.schemas.comments import CommentCreate, CommentRead, CommentUpdate

post_router = APIRouter(prefix="/posts", tags=["comments"])
comment_router = APIRouter(prefix="/comments", tags=["comments"])


def get_existing_post(post_id: int, db: DbSession) -> Post:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException( 
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )
    return post


@post_router.get("/{post_id}/comments", response_model=list[CommentRead])
def list_comments(post_id: int, db: DbSession) -> list[Comment]:
    get_existing_post(post_id, db)
    statement = (
        select(Comment)
        .where(Comment.post_id == post_id)
        .order_by(Comment.created_at, Comment.id)
    )
    return list(db.scalars(statement).all())


@post_router.post(
    "/{post_id}/comments",
    response_model=CommentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    post_id: int,
    payload: CommentCreate,
    db: DbSession,
    current_user: CurrentUser,
) -> Comment:
    get_existing_post(post_id, db)
    comment = Comment(
        content=payload.content,
        post_id=post_id,
        author_id=current_user.id,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@comment_router.put("/{comment_id}", response_model=CommentRead)
def update_comment(
    comment_id: int,
    payload: CommentUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> Comment:
    comment = db.scalar(
        select(Comment).where(
            Comment.id == comment_id,
            Comment.author_id == current_user.id,
        )
    )
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )
    comment.content = payload.content
    db.commit()
    db.refresh(comment)
    return comment


@comment_router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_comment(
    comment_id: int,
    db: DbSession,
    current_user: CurrentUser,
) -> Response:
    comment = db.scalar(
        select(Comment).where(
            Comment.id == comment_id,
            Comment.author_id == current_user.id,
        )
    )
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )
    db.delete(comment)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
