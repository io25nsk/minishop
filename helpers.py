from fastapi import BackgroundTasks
import asyncio
from datetime import datetime as dt
from bson.objectid import ObjectId
from database import USERS_COLLECTION, ORDER_COLLECTION, CARTS_COLLECTION, PRODUCTS_COLLECTION, PROMOCODES_COLLECTION
from models import Cart, Order, ProductReturn
import paysystem_mock


def product_helper(product) -> dict:
    """
    Return product with converted to str _id.
    """
    product['id'] = str(product.pop('_id'))
    return product


async def get_user_cid(data: Cart | Order = None, _uid: str = None) -> str | None:
    """
    Return cid of cart for user with that uid.
    """
    uid = _uid if _uid else data.uid
    user = await USERS_COLLECTION.find_one({'_id': ObjectId(uid)})
    if user:
        return user['cid']


async def order_pay_timer(seconds: int, oid: str) -> None:
    """
    Wait number of seconds and check order oid, if order not paid, set status "Expired".
    """
    await asyncio.sleep(seconds)
    order = await ORDER_COLLECTION.find_one({'_id': ObjectId(oid)})
    if order['status'] == 'Created':
        order['status'] = 'Expired'
        await ORDER_COLLECTION.update_one({'_id': ObjectId(oid)}, {'$set': order})


async def cart_helper(cid: str) -> dict:
    """
    Return cart for that uid.
    """
    cart = await CARTS_COLLECTION.find_one({"_id": ObjectId(cid)})
    result = {'id': str(cart['_id']),
              'products': [],
              'total': cart['total']}

    for item in cart['products']:
        pid = item['pid']
        quantity = item['quantity']
        summ = item['summ']
        product = await PRODUCTS_COLLECTION.find_one({'_id': ObjectId(pid)})
        product = product_helper(product)
        product['quantity'] = quantity
        product['summ'] = summ
        result['products'] += [product]

    return result


async def cart_add_helper(data: Cart, cid: str) -> dict:
    """
    Add to cart of user with uid quantity of products with pid.
    """
    uid, pid, quantity = data.model_dump().values()
    cart = await CARTS_COLLECTION.find_one({'_id': ObjectId(cid)})
    product = await PRODUCTS_COLLECTION.find_one({'_id': ObjectId(pid)})

    if product:
        price = product['price']
        products = cart['products']
        total = cart['total']
        pids_list = [p['pid'] for p in products]

        if pid in pids_list:
            product_index = pids_list.index(pid)
            products[product_index]['price'] = price
            products[product_index]['quantity'] += quantity
            products[product_index]['summ'] += quantity * price
        else:
            products += [{'pid': pid,
                          'price': price,
                          'quantity': quantity,
                          'summ': quantity * price}]

        total += price * quantity
        result = await CARTS_COLLECTION.update_one({'_id': ObjectId(cid)},
                                                   {'$set': {'products': products, 'total': total}})

        if result.acknowledged:
            return {'status': f'Products {pid} added to cart of user {uid}'}
        else:
            return {'error': f'Products {pid} not added to cart of user {uid}'}

    else:
        return {"error": f"Product {pid} not found!"}


async def cart_del_helper(uid, cid, pid, quantity) -> dict:
    """
    Remove product with pid from cart for user with uid.
    """
    cart = await CARTS_COLLECTION.find_one({'_id': ObjectId(cid)})
    product = await PRODUCTS_COLLECTION.find_one({'_id': ObjectId(pid)})

    if product:
        price = product['price']
        products = cart['products']
        total = cart['total']
        pids_list = [p['pid'] for p in products]

        if pid in pids_list:
            product_index = pids_list.index(pid)

            if products[product_index]['quantity'] < quantity:
                return {'error': f'Quantity {quantity} of product {pid} is greater than quantity in cart of user {uid}'}
            elif products[product_index]['quantity'] == quantity:
                products.pop(product_index)
            else:
                products[product_index]['quantity'] -= quantity
                products[product_index]['summ'] -= price * quantity
            total -= price * quantity
            result = await CARTS_COLLECTION.update_one({'_id': ObjectId(cid)},
                                                       {'$set': {'products': products, 'total': total}})

            if result.acknowledged:
                return {'status': f'Products {pid} with {quantity} removed from cart of user {uid}'}
            else:
                return {'error': f'Products {pid} not removed from cart of user {uid}'}

        else:
            return {'error': f'Product {pid} not found in cart for user {uid}'}

    else:
        return {"error": f"Product {pid} not found!"}


async def order_add_helper(data: Order, cid: str, background_task: BackgroundTasks) -> dict:
    """
    Create order from cart for user with that uid.
    """
    global_discount = 0
    uid, promocodes, pay_timeout = data.model_dump().values()
    cart = await CARTS_COLLECTION.find_one({"_id": ObjectId(cid)})
    products = cart['products']
    extra_fields = {'discount': 0,
                    'discount_summ': 0,
                    'summ_with_discount': 0,
                    'return_quantity': 0,
                    'return_summ': 0,
                    'return_status': None,
                    'return_dates': []}

    if not products:
        return {'error': f'Cart {cid} is empty.'}

    pids_list = [p['pid'] for p in products]
    order = {'uid': uid,
             'date': dt.now().isoformat(),
             'products': cart['products'],
             'promocodes': promocodes,
             'global_discount': 0,
             'global_discount_summ': 0,
             'total': cart['total'],
             'total_with_discount': cart['total'],
             'status': 'Created',
             'pay_date': None,
             'pay_id': None,
             'pay_status': None,
             'pay_system': None}

    for product in products:
        product.update(extra_fields)

    for promocode in promocodes:
        code = await PROMOCODES_COLLECTION.find_one({"code": promocode})

        if code:
            pid = code['pid']

            if pid == 'Global':
                global_discount = code['discount']
            elif pid in pids_list:
                product = products[pids_list.index(pid)]
                discount = code['discount']
                product['discount'] = discount
                product['discount_summ'] = product['summ'] * discount
                product['summ_with_discount'] = product['summ'] - product['discount_summ']
                order['total'] -= product['discount_summ']
            else:
                pass

            order['global_discount'] = global_discount
            order['global_discount_summ'] = order['total'] * global_discount
            order['total_with_discount'] = order['total'] - order['global_discount_summ']

        else:
            return {'error': f'Promocode {promocode} not found'}

    result_order = await ORDER_COLLECTION.insert_one(order)

    if result_order:
        await CARTS_COLLECTION.update_one({'_id': ObjectId(cid)}, {'$set': {'products': [], 'total': 0}})
        oid = result_order.inserted_id

        if pay_timeout:
            background_task.add_task(order_pay_timer, pay_timeout, oid)

        return {'status': f'Order {oid} created.'}
    else:
        return {'error': f'Order for {cid} not created.'}


async def order_pay_helper(oid: str, pay_system: str) -> dict:
    """
    Pay order with that data.
    """
    order = await ORDER_COLLECTION.find_one({"_id": ObjectId(oid)})

    if order['status'] in ('Paid', 'Returned'):
        return {'error': f'Order {oid} already paid.'}
    elif order['status'] == 'Expired':
        return {'error': f'Order {oid} expired.'}

    pay_summ = order['total_with_discount']
    pay_result = paysystem_mock.send_payment(oid, pay_summ, pay_system)

    if pay_result['pay_status'] == 'Successful':
        result = {'status': 'Paid',
                  'pay_id': pay_result['pay_id'],
                  'pay_date': pay_result['pay_date'],
                  'pay_system': pay_system,
                  'pay_status': pay_result['pay_status']}
        await ORDER_COLLECTION.update_one({'_id': ObjectId(oid)}, {'$set': result})
        return {'status': f'Order {oid} is paid.'}
    else:
        return {'error': f'Order {oid} not paid.'}


async def order_return_helper(oid: str, data: ProductReturn) -> dict:
    """
    Return products from order with that oid.
    """
    pid, quantity = data.model_dump().values()
    order = await ORDER_COLLECTION.find_one({'_id': ObjectId(oid)})

    if order['status'] not in ('Paid', 'Returned'):
        return {'error': f'Order {oid} is not paid.'}

    products = order['products']
    order_pids = [product['pid'] for product in products]

    if pid not in order_pids:
        return {'error': f'Product {pid} not in order {oid}.'}
    else:
        returned_product = products[order_pids.index(pid)]

    if quantity > returned_product['quantity'] - returned_product['return_quantity']:
        return {'error': f'Quantity {quantity} of product {pid} more then in order {oid}.'}

    returned_product['return_quantity'] += quantity
    returned_product['return_summ'] += (quantity *
                                        returned_product['price'] *
                                        (1 - returned_product['discount']) *
                                        (1 - order['global_discount']))
    returned_product['return_status'] = 'Returned'
    returned_product['return_dates'] += [dt.now().isoformat()]
    order['status'] = 'Returned'

    if paysystem_mock.return_payment(order['pay_id'],
                                     returned_product['return_summ'],
                                     order['pay_system'])['pay_status'] == 'Successful':
        result = await ORDER_COLLECTION.update_one({'_id': ObjectId(oid)}, {'$set': order})

        if result.acknowledged:
            return {'status': f'Product {pid} in quantity {quantity} is returned'}
        else:
            return {'error': f'Product {pid} in quantity {quantity} is not returned'}

    else:
        return {'error': f'Payment is not returned.'}


async def order_return_status_helper(order: dict) -> list | dict:
    """
    Return status of returned products for that oid.
    """
    if order['status'] == 'Returned':
        result = [{'pid': product['pid'],
                   'return_status': product['return_status']}
                  for product in order['products'] if product['return_status'] == 'Returned']
        return result
    else:
        return {'error': f'No returned products in order {str(order["_id"])}'}
