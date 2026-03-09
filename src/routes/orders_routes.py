from fastapi import APIRouter, status, Depends
from sqlalchemy.orm import Session

from db.db import get_session
from schemas.order_schema import OrderResponseSchema, OrderCreateSchema
from schemas.user_schema import TokenSchema
from services import order_service

orders_router = APIRouter(tags=["Orders Routes"])


@orders_router.post(
    "/", response_model=OrderResponseSchema, status_code=status.HTTP_201_CREATED
)
def create_order(
    payload: OrderCreateSchema,
    token: TokenSchema,
    session: Session = Depends(get_session),
):
    return order_service.create_order(session, payload, token)
