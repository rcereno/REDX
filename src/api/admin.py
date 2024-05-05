import sqlalchemy
import database as db

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
import auth

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the shop state. Carts are all reset.
    """

    return "OK"
