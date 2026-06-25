from fastapi import FastAPI

from app.routers.client_router import router as client_router
from app.routers.clients import router as clients_router
from app.routers.departments import router as department_router
from app.routers.platform_admin_router import router as platform_admin_router
from app.routers.role_permission import router as role_permissions_router
from app.routers.roles import router as roles_router
from app.routers.services import router as services_router
from app.routers.subscription import router as subscription_router
from app.routers.location import router as location_router
from app.routers.users import router as users_router
from fastapi.middleware.cors import CORSMiddleware
from app.config import cloudinary


from app.routers import auth


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # testing ke liye
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(location_router)
app.include_router(auth.router)
app.include_router(platform_admin_router)
app.include_router(clients_router)
app.include_router(client_router)
app.include_router(role_permissions_router)
app.include_router(roles_router)
app.include_router(department_router)

app.include_router(subscription_router)
app.include_router(users_router)
app.include_router(services_router)
from app.routers import asset, asset_categories, asset_type, dashboard

app.include_router(
    asset_categories.router
)
app.include_router(asset_type.router)
app.include_router(dashboard.router)



from app.routers import asset

app.include_router(
    asset.router
)

from app.routers import manager

app.include_router(
    manager.router
)

@app.get("/")
def test():
    return {"message": "started"}