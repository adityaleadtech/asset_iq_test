from datetime import datetime,timedelta
from jose import jwt

from app.config.settings import settings


def create_token(data:dict):
    to_encode=data.copy()

    expire=datetime.utcnow()+timedelta(
        minutes=settings.EXPIRY
    )

    to_encode.update({
        "exp":expire
    })

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

