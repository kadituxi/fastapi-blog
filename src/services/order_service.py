from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from repositories import order_repository
from schemas.order_schema import OrderCreateSchema
from schemas.user_schema import TokenSchema
from services.product_service import get_product_by_id
from services.user_service import get_user


def create_order(session: Session, payload: OrderCreateSchema, token: TokenSchema):
    product = get_product_by_id(session, payload.product_id)
    if not product or product.qtd_stock < payload.qtd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Produto não encontrado ou qtd superior à qtd disponível",
        )
    user = get_user(token.access_token, session)
    order = order_repository.create_order(session, payload, user.id)
    product = order.product
    product.qtd_stock -= payload.qtd
    session.commit()
    return order
