from fastapi import FastAPI
from app.routers.platform_admin_router import router as platform_admin_router


app= FastAPI()

app.include_router(platform_admin_router)

from app.routers.clients import (
    router as client_router
)
app.include_router(platform_admin_router)
app.include_router(client_router)


@app.get("/")
def test():
    return {"message":"started"}

