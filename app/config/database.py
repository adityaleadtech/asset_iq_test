from sqlalchemy import create_engine 
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

from app.config.settings import settings

DATABASE_URL = (
    f"mysql+pymysql://"
    f"{settings.DB_USER}:"
    f"{settings.DB_PASSWORD}@"
    f"{settings.DB_HOST}:"
    f"{settings.DB_PORT}/"
    f"{settings.DB_NAME}"
    f"?ssl_disabled=true"
)
#creates a connection engine that SQLAlchemy  uses to communicate with the database
engine= create_engine(
    DATABASE_URL,
    echo=True
)


# sessionmaker creates Session objects.
# These sessions are used for database operations
# eg : db=SessionLocal()
# such as db.add(), db.query(), db.commit(), etc.

SessionLocal= sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

#creates a parent class for all the database models 
#without this SQLAlchemy would not know if the class is a table 
Base= declarative_base()