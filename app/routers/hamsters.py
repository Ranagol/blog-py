from fastapi import APIRouter, HTTPException, Query, Response, status
from sqlalchemy import desc, select

from app.dependencies import CurrentUser, DbSession
from app.models import Hamster  # sqlalchemy models
from app.schemas.hamsters import HamsterCreate  # pydantic schemas

router = APIRouter(prefix="/hamsters", tags=["hamsters"])

# LIST HAMSTERS
@router.get('/hamsters', tags=['hamsters'])
def list_hamsters(
    name: str | None = Query(default=None, min_length=2, max_length=30)
):
    if name:
        return {"name": name}
    return None

# GET HAMSTER BY ID
@router.get('/hamsters/{hamster_id}', tags=['hamsters'])
def get_hamster(hamster_id: int):
    return {"id": hamster_id}





# CREATE
@router.post('/hamsters', tags=['hamsters'])
def create_hamster(payload: HamsterCreate):
    return payload