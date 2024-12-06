from motor.motor_asyncio import AsyncIOMotorClient

DB_URI = 'mongodb://localhost:27017/'
CLIENT = AsyncIOMotorClient(DB_URI)
DB = CLIENT.minishop
USERS_COLLECTION = DB.users
PRODUCTS_COLLECTION = DB.products
CARTS_COLLECTION = DB.carts
ORDER_COLLECTION = DB.orders
PROMOCODES_COLLECTION = DB.promocodes
