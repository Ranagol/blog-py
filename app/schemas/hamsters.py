

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.base import RequestModel


class HamsterCreate(RequestModel):
    name: str
    age: int
    color: str

class HamsterUpdate(RequestModel):
    name: str | None = None
    age: int | None = None
    color: str | None = None
    user_id: int | None = None

class HamsterRead(BaseModel):
    id: int
    name: str
    age: int
    color: str
    user_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)