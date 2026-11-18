from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from datetime import datetime


class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UserCredentials(RequestModel):
    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value

class UserCreate(UserCredentials):
    pass


class UserRead(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


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


class AuthorRead(BaseModel):
    id: int

    model_config = ConfigDict(from_attributes=True)


class PostRead(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime
    author: AuthorRead

    model_config = ConfigDict(from_attributes=True)


class CommentRead(BaseModel):
    id: int
    content: str
    created_at: datetime
    updated_at: datetime
    post_id: int
    author: AuthorRead

    model_config = ConfigDict(from_attributes=True)
