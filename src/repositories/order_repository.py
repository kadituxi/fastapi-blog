from sqlalchemy.orm import Session

from models.order import Order
from schemas.order_schema import OrderCreateSchema


def create_order(session: Session, payload: OrderCreateSchema, user_id: int) -> Order:
    order = Order(**payload.model_dump())
    order.user_id = user_id
    session.add(order)
    session.commit()
    session.refresh(order)
    return order
