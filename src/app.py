from fastapi import FastAPI
import uvicorn

from routes import products_routes, users_routes, orders_routes
# from db.db import Base, engine
# from models import order_model, product_model, user_model

app = FastAPI(
    title="Kadituxi Store API",
    description="Kadituxi Store - API for orders management.",
    version="1.0",
)

app.include_router(router=users_routes.users_router, prefix="/api/v1/users")
app.include_router(router=products_routes.products_router, prefix="/api/v1/products")
app.include_router(router=orders_routes.orders_router, prefix="/api/v1/orders")


if __name__ == "__main__":
    # Base.metadata.create_all(engine)
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

