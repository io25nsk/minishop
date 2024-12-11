from motor.motor_asyncio import AsyncIOMotorClient
from settings import settings

CLIENT = AsyncIOMotorClient(settings.DB_URI)
DB = CLIENT.minishop
USERS_COLLECTION = DB.users
PRODUCTS_COLLECTION = DB.products
CARTS_COLLECTION = DB.carts
ORDER_COLLECTION = DB.orders
PROMOCODES_COLLECTION = DB.promocodes
