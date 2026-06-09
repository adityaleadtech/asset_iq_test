from sqlalchemy import text

from app.config.database import engine

try:
    #engine.connect() connects to the database
    with engine.connect() as connection:
        #connection.execute executes raw sql queries with text()
        result= connection.execute(text("SELECT 1"))
        print("DATABASE CONNECTED")
        print(result.scalar())


except Exception as e:
    print("Database connections failed")
    print(e)