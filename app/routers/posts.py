from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import asc, desc, or_, select

from app.dependencies import CurrentUser, DbSession
from app.models import Post  # sqlalchemy models
from app.schemas.posts import PostCreate, PostRead, PostUpdate  # pydantic schemas

router = APIRouter(prefix="/posts", tags=["posts"])

# LIST ALL
@router.get("", response_model=Page[PostRead]) # Page is needed for pagination
def list_posts(
    db: DbSession,
    search: str | None = Query(default=None, min_length=1, max_length=100),
    author_id: int | None = None,
    # Literal ensures that only the specified values are allowed for sort_by and order
    sort_by: Literal["created_at", "title"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
) -> Page[Post]: # Page is needed for pagination

    column, direction = sort(sort_by, order)

    statement = setSearchStatement(search, author_id)

    # direction is either asc or desc +(), that makes them a function from SQLAlchemy
    statement = statement.order_by(direction(column), direction(Post.id))
    
    return paginate(db, statement)


# Helper function for building the search statement based on search and author_id filters
def setSearchStatement(search, author_id):
    statement = select(Post)

    if search is not None:
        pattern = f"%{search}%"
        statement = statement.where(
            or_(
                Post.title.ilike(pattern),
                Post.content.ilike(pattern),
            )
        )

    if author_id is not None:
        statement = statement.where(Post.author_id == author_id)
    return statement


# Helper function for sort. Transforms sorting data from FE to corresponding SQLAlchemy column and direction
def sort(sort_by, order):
    # We transform here the value of sort fron FE (unsecure) to the corresponding SQLAlchemy column
    SORT_COLUMNS = {
        "created_at": Post.created_at,
        "title": Post.title,
    }

    # From SORT_COLUMNS dictionary we get by key (title or created_at) the corresponding 
    # Post.created_at or Post.title column
    column = SORT_COLUMNS[sort_by]
    direction = desc if order == "desc" else asc
    return column,direction


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
