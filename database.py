from motor.motor_asyncio import AsyncIOMotorClient

db_uri = 'mongodb://localhost:27017/'
client = AsyncIOMotorClient(db_uri)
db = client.minishop
users_collection = db.users
products_collection = db.products
carts_collection = db.carts
orders_collection = db.orders
promocodes_collection = db.promocodes
