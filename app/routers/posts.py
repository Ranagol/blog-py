from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import desc, select

from app.dependencies import CurrentUser, DbSession
from app.models import Post  # sqlalchemy models
from app.schemas.posts import PostCreate, PostRead, PostUpdate  # pydantic schemas

router = APIRouter(prefix="/posts", tags=["posts"])

# LIST ALL
@router.get("", response_model=list[PostRead])
def list_posts(db: DbSession) -> list[Post]:
    statement = select(Post).order_by(desc(Post.created_at), desc(Post.id))
    return list(db.scalars(statement).all())

# GET POST
@router.get("/{post_id}", response_model=PostRead)
def get_post(post_id: int, db: DbSession) -> Post:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )
    return post

# CREATE POST
# create_post return Post sqlalchemy model. This will be serialized to PostRead pydantic schema in the response.
@router.post("", response_model=PostRead, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate, db: DbSession, current_user: CurrentUser) -> Post:
    post = Post(
        title=payload.title,
        content=payload.content,
        author_id=current_user.id,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

# UPDATE POST
@router.put("/{post_id}", response_model=PostRead)
def update_post(
    post_id: int,
    payload: PostUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> Post:
    post = db.scalar(
        select(Post).where(
            Post.id == post_id,
            Post.author_id == current_user.id,
        )
    )
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )

    post.title = payload.title
    post.content = payload.content
    db.commit()
    db.refresh(post)
    return post

# DELETE POST
@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_post(post_id: int, db: DbSession, current_user: CurrentUser) -> Response:
    post = db.scalar(
        select(Post).where(
            Post.id == post_id,
            Post.author_id == current_user.id,
        )
    )
    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )
    db.delete(post)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
