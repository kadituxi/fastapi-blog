from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BaseProductSchema(BaseModel):
    name: str = Field(min_length=3)
    description: str = Field(min_length=5)
    qtd_stock: int = Field(ge=0)
    price: float = Field(ge=1)


class ProductCreateSchema(BaseProductSchema):
    pass


class ProductUpdateSchema(BaseProductSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    qtd_stock: Optional[int] = None
    price: Optional[float] = None


class ProductResponseSchema(BaseProductSchema):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
