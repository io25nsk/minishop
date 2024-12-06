import uvicorn
from typing import Annotated
from bson.objectid import ObjectId
from fastapi import FastAPI, BackgroundTasks, Path
from pydantic import AfterValidator

import helpers
from database import ORDER_COLLECTION, PRODUCTS_COLLECTION
from models import Cart, Order, ProductReturn, PayData, check_common_ids

app = FastAPI()


@app.get("/products/")
async def get_all_products() -> list | dict:
    """
    Return all products.
    """
    result = []
    all_products = PRODUCTS_COLLECTION.find()

    if all_products:
        for product in await all_products.to_list():
            result += [helpers.product_helper(product)]
        return result
    else:
        return {"error": "No products found!"}


@app.get("/products/{pid}/")
async def get_product(
    pid: str = Path(annotation=Annotated[str, AfterValidator(check_common_ids)]),
) -> dict:
    """
    Return product with that pid.
    """
    product = await PRODUCTS_COLLECTION.find_one({"_id": ObjectId(pid)})

    if product:
        return helpers.product_helper(product)
    else:
        return {"error": f"Product {pid} not found!"}


@app.get("/cart/{uid}/")
async def get_cart(
    uid: str = Path(annotation=Annotated[str, AfterValidator(check_common_ids)]),
) -> dict:
    """
    Return cart for that uid.
    """
    cid = await helpers.get_user_cid(_uid=uid)

    if cid:
        return await helpers.cart_helper(cid)
    else:
        return {"error": f"User {uid} not found"}


@app.post("/cart/add/")
async def add_to_cart(data: Cart) -> dict:
    """
    Add to cart of user with uid quantity of products with pid.
    """
    cid = await helpers.get_user_cid(data)

    if cid:
        return await helpers.cart_add_helper(data, cid)
    else:
        return {"error": f"User {data.uid} not found"}


@app.delete("/cart/remove/{uid}/{pid}/{quantity}/")
async def del_from_cart(
    quantity: Annotated[int, Path(ge=1)],
    uid: str = Path(annotation=Annotated[str, AfterValidator(check_common_ids)]),
    pid: str = Path(annotation=Annotated[str, AfterValidator(check_common_ids)]),
) -> dict:
    """
    Remove quantity of product with pid from cart for user with uid.
    """
    cid = await helpers.get_user_cid(_uid=uid)

    if cid:
        return await helpers.cart_del_helper(uid, cid, pid, quantity)
    else:
        return {"error": f"User {uid} not found"}


@app.get("/order/{uid}/")
async def get_user_orders(
    uid: str = Path(annotation=Annotated[str, AfterValidator(check_common_ids)]),
) -> list | dict:
    """
    Return orders for that uid.
    """
    result = []
    orders = ORDER_COLLECTION.find({"uid": uid})

    for order in await orders.to_list():
        order["id"] = str(order.pop("_id"))
        result += [order]

    if result:
        return result
    else:
        return {"error": f"No orders found for user {uid}"}


@app.post("/order/create/")
async def create_order(data: Order, background_task: BackgroundTasks) -> dict:
    """
    Create order from cart for user with that uid.
    """
    cid = await helpers.get_user_cid(data)

    if cid:
        return await helpers.order_add_helper(data, cid, background_task)
    else:
        return {"error": f"User {data.uid} not found"}


@app.post("/order/pay/")
async def pay_order(data: PayData) -> dict:
    """
    Pay order with that data.
    """
    oid, pay_system = data.model_dump().values()
    return await helpers.order_pay_helper(oid, pay_system)


@app.post("/order/{oid}/return/")
async def return_order(
    data: ProductReturn,
    oid: str = Path(annotation=Annotated[str, AfterValidator(check_common_ids)]),
) -> dict:
    """
    Return products from order with that oid.
    """
    order = await ORDER_COLLECTION.find_one({"_id": ObjectId(oid)})

    if order:
        return await helpers.order_return_helper(oid, data)
    else:
        return {"error": f"Order {oid} not found."}


@app.get("/order/{oid}/return_status/")
async def status_return_order(
    oid: str = Path(annotation=Annotated[str, AfterValidator(check_common_ids)]),
) -> list | dict:
    """
    Return status of returned products for that oid.
    """
    order = await ORDER_COLLECTION.find_one({"_id": ObjectId(oid)})

    if order:
        return await helpers.order_return_status_helper(order)
    else:
        return {"error": f"Order {oid} not found."}


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
