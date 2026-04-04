import datetime

from sqlalchemy import Column, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship

from db.db import Base


class Order(Base):
    __tablename__ = "order"

    id = Column(Integer, primary_key=True, index=True)
    qtd = Column(Integer)
    product_id = Column(Integer, ForeignKey("product.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))

    created_at = Column(DateTime, default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, onupdate=datetime.datetime.now(datetime.timezone.utc))

    product = relationship("Product", backref="orders")
    user = relationship("User", backref="orders")

