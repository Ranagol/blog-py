from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.schemas.base import AuthorRead, RequestModel


class PostCreate(RequestModel):
    title: str
    content: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Title must contain a non-whitespace character")
        return value

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Content must contain a non-whitespace character")
        return value


class PostUpdate(PostCreate):
    pass

class PostRead(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    author: AuthorRead

    model_config = ConfigDict(from_attributes=True)