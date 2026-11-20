from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.base import AuthorRead, RequestModel


class CommentCreate(RequestModel):
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Content must contain a non-whitespace character")
        return value


class CommentUpdate(CommentCreate):
    pass


class CommentRead(BaseModel):
    id: int
    content: str
    created_at: datetime
    updated_at: datetime
    post_id: int
    author: AuthorRead

    model_config = ConfigDict(from_attributes=True)