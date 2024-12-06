from httpx import ASGITransport, AsyncClient
from main import app
import pytest

exist_pid = "6707956239445e8693a16362"
not_exist_pid = "6707956239475e8693a16362"
bad_pid = "6707956239445e8693z16362"
not_return_pid = "6707956239445e8693a16363"

exist_uid = "671210a24c0b7d4a8caa715a"
not_exist_uid = "671210a24c0b8d4a8caa715a"
bad_uid = "671210a24c0b7d4a8caa715z"

exist_oid = "672d5863097669defb54b2d4"
not_exist_oid = "672ba75c945f8633ca615962"
bad_oid = "672ba75c945f1633cz615962"
new_oid = ""
expired_oid = "672d57755ea648a1bff8ad08"

promocodes = ["IPHONE15", "MINISHOP20"]


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


# Products
@pytest.mark.anyio
async def test_get_all_products(client):
    response = await client.get("/products/")
    assert isinstance(response.json(), list)


@pytest.mark.anyio
async def test_get_exist_product(client):
    response = await client.get(f"/products/{exist_pid}/")
    assert "error" not in response.json()


@pytest.mark.anyio
async def test_get_non_exist_product(client):
    response = await client.get(f"/products/{not_exist_pid}/")
    assert "error" in response.json()


@pytest.mark.anyio
async def test_get_product_bad_pid(client):
    response = await client.get(f"/products/{bad_pid}/")
    assert response.status_code == 422


# Carts
@pytest.mark.anyio
async def test_get_exist_uid(client):
    response = await client.get(f"/cart/{exist_uid}/")
    assert "error" not in response.json()


@pytest.mark.anyio
async def test_get_not_exist_uid(client):
    response = await client.get(f"/cart/{not_exist_uid}/")
    assert "error" in response.json()


@pytest.mark.anyio
async def test_get_cart_bad_uid(client):
    response = await client.get(f"/cart/{bad_uid}/")
    assert response.status_code == 422


@pytest.mark.anyio
async def test_add_cart(client):
    response = await client.post(
        "/cart/add/", json={"uid": exist_uid, "pid": exist_pid, "quantity": 3}
    )

    assert "error" not in response.json()


@pytest.mark.anyio
async def test_del_cart_more_quantity(client):
    response = await client.delete(f"/cart/remove/{exist_uid}/{exist_pid}/{100}/")
    assert "error" in response.json()


@pytest.mark.anyio
async def test_del_cart_normal_quantity(client):
    response = await client.delete(f"/cart/remove/{exist_uid}/{exist_pid}/{1}/")
    assert "error" not in response.json()


# Orders
@pytest.mark.anyio
async def test_get_orders(client):
    response = await client.get(f"/order/{exist_uid}/")
    assert "error" not in response.json()


@pytest.mark.anyio
async def test_get_orders_not_exist_uid(client):
    response = await client.get(f"/order/{not_exist_uid}/")
    assert "error" in response.json()


@pytest.mark.anyio
async def test_get_orders_bad_uid(client):
    response = await client.get(f"/order/{bad_uid}/")
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_order(client):
    global new_oid
    response = await client.post(
        "/order/create/",
        json={"uid": exist_uid, "promocodes": promocodes, "pay_timeout": 0},
    )
    assert "error" not in response.json()
    new_oid = response.json()["status"].split()[1]


@pytest.mark.anyio
async def test_pay_order(client):
    response = await client.post(
        "/order/pay/", json={"oid": new_oid, "pay_system": "VISA"}
    )
    assert "error" not in response.json()


@pytest.mark.anyio
async def test_pay_expired_order(client):
    response = await client.post(
        "/order/pay/", json={"oid": expired_oid, "pay_system": "VISA"}
    )
    assert "error" in response.json()


# Returns
@pytest.mark.anyio
async def test_order_return_expired(client):
    response = await client.post(
        f"/order/{expired_oid}/return/", json={"pid": exist_pid, "quantity": 1}
    )
    assert "error" in response.json()


@pytest.mark.anyio
async def test_order_return_more_quantity(client):
    response = await client.post(
        f"/order/{new_oid}/return/", json={"pid": exist_pid, "quantity": 100}
    )
    assert "error" in response.json()


@pytest.mark.anyio
async def test_order_return(client):
    response = await client.post(
        f"/order/{new_oid}/return/", json={"pid": exist_pid, "quantity": 1}
    )
    assert "error" not in response.json()


@pytest.mark.anyio
async def test_order_return_not_product(client):
    response = await client.post(
        f"/order/{exist_oid}/return/", json={"pid": not_return_pid, "quantity": 1}
    )
    assert "error" in response.json()


@pytest.mark.anyio
async def test_get_return_status(client):
    response = await client.get(f"/order/{new_oid}/return_status/")
    assert "error" not in response.json()


@pytest.mark.anyio
async def test_get_return_status_not_exist_oid(client):
    response = await client.get(f"/order/{not_exist_oid}/return_status/")
    assert "error" in response.json()


@pytest.mark.anyio
async def test_get_return_status_bad_oid(client):
    response = await client.get(f"/order/{bad_oid}/return_status/")
    assert response.status_code == 422
