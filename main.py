from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

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
from app.routers.map import router as map_router
from app.routers import auth, asset, asset_categories, asset_type, dashboard, manager
from app.routers.authentication import router as authentication_router
from app.routers.profile import router as profile_router
from app.routers.tracking import router as tracking_router
from app.routers.audit import router as audit_router


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================
# COMMON API ROUTER with /api prefix
# ============================================
api_router = APIRouter(prefix="/api")

# Add all routers to the common api_router
api_router.include_router(tracking_router)
api_router.include_router(location_router)
api_router.include_router(auth.router)
api_router.include_router(platform_admin_router)
api_router.include_router(clients_router)
api_router.include_router(client_router)
api_router.include_router(role_permissions_router)
api_router.include_router(roles_router)
api_router.include_router(department_router)
api_router.include_router(subscription_router)
api_router.include_router(users_router)
api_router.include_router(services_router)
api_router.include_router(asset_categories.router)
api_router.include_router(asset_type.router)
api_router.include_router(dashboard.router)
api_router.include_router(asset.router)
api_router.include_router(manager.router)
api_router.include_router(authentication_router)
api_router.include_router(map_router)
api_router.include_router(profile_router)
api_router.include_router(audit_router)

app.include_router(api_router)

# Include the common router in the app


# ============================================
# ROOT ENDPOINTS (no /api prefix)
# ============================================
@app.get("/")
def test():
    return {"message": "started"}

@app.get("/api")
def api_root():
    return {"message": "API is running. All endpoints are under /api/*"}