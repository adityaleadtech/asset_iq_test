from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.dependencies import (
    get_db,
    get_current_user
)

from app.schemas.dashboards import (
    ClientDashboardResponse
)

from app.services.dashboards import (
    get_client_dashboard
)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get(
    "/client",
    response_model=ClientDashboardResponse,
    summary="Client Dashboard",
    description="""
    Returns dashboard metrics.

    Access:
    - ADMIN
    - CLIENT_ADMIN

    CLIENT_ADMIN:
    - Can view dashboard of their own client

    ADMIN:
    - Can view dashboard of any client
    - Must pass client_id query parameter

    Dashboard Metrics:
    - Total Users
    - Active Users
    - Total Departments
    - Total Assets

    Subscription Information:
    - Maximum Assets Allowed
    - Maximum Departments Allowed
    - Licence Count
    - Used Licences

    Examples:

    CLIENT_ADMIN:
    GET /dashboard/client

    ADMIN:
    GET /dashboard/client?client_id=<client_uuid>
    """
)
def client_dashboard(
    client_id: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(
        get_current_user
    )
):

    return get_client_dashboard(
        db,
        current_user,
        client_id
    )