from app.config.database import SessionLocal
from app.models.clients import Client

db = SessionLocal()

clients = db.query(Client).all()

print(clients)