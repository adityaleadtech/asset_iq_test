from fastapi import FastAPI

from app.routers.platform_admin_router import (
    router as platform_admin_router
)

from app.routers.subscription import (
    router as subscription_router
)

from app.routers.subscription_plans import (
    router as subscription_plan_router
)

from app.routers.client_router import (
    router as client_admin_router
)


from app.routers.clients import (
    router as clients_router
)

from app.routers.client_router import (
    router as client_admin_router
)

from app.routers.departments import (
    router as department_router
)


app = FastAPI()

app.include_router(platform_admin_router)

app.include_router(clients_router)

app.include_router(client_admin_router)

app.include_router(
    client_admin_router
)


app.include_router(
    department_router
)

app.include_router(
    subscription_plan_router
)

app.include_router(
    subscription_router
)

from app.routers.users import (
    router as user_router
)
from app.routers.services import router as services_router

app.include_router(user_router)

app.include_router(services_router)


@app.get("/")
def test():
    return {
        "message": "started"
    }


