Test project for REST API - implementation of a shopping cart system with payment and return of goods based on FastAPI and MongoDB.

Full technical information about that task contain in file task.txt (in russian language).

For use this project you need copy that to your HDD by any methods you like: git, download zip, etc.

Open project in your favorite IDE.

Install all needed requirements by:
pip install -r requirements.txt

You will also need MongoDB installed: create a "minishop" database and import all the collections from the files in the "json" directory into it.

Create a file called .env in your project root directory and put your MongoDB connection information in it, minimal like this:
DB_URI = "mongodb://localhost:27017/"
change host, port if it needed.

If you need it can be extended by adding username, password, some database settings.

Finally, run project: 
uvicorn.exe main:app --reload
