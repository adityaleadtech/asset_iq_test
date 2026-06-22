from pydantic_settings import BaseSettings

# This file manages application configuration settings
# such as database credentials and other environment variables.
# pydantic_settings gives BaseSettings that verifies if the fields are of correct data type or not

class Settings(BaseSettings):
    DB_USER:str
    DB_HOST:str
    DB_PORT:int
    DB_NAME:str
    DB_PASSWORD:str
    SECRET_KEY: str
    ALGORITHM: str
    EXPIRY: int

    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    RESEND_API_KEY: str
    FRONTEND_URL: str


    #this class tells where to read the values from 
    #read the values from .env file
    #without the Config class it would read the data from OS env variables
    #with this the variables are read from .env file
    class Config:
        env_file=".env"

# Create a Settings object.
# Pydantic reads values from .env, validates them,
# and stores them in this object.
# This object can be imported throughout the application.
settings=Settings()
