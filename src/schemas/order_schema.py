from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BaseOrderSchema(BaseModel):
    qtd: float = Field(ge=1)
    product_id: int


class OrderCreateSchema(BaseOrderSchema):
    pass


class OrderResponseSchema(BaseOrderSchema):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
