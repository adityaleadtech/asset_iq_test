from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.config.dependencies import get_db

from app.schemas.clients import (
    ClientCreate,
    ClientResponse,
    ClientUpdate
)

from app.config.dependencies import (
    get_current_user
)

from app.services.client_services import (
    create_client,
    get_all_clients,
    get_client_by_id,
    get_subscription_services,
    update_client,
    delete_client,
    get_deactivated_clients,
    reactivate_client
)

from app.services.subscription import get_client_subscription_status
from app.utils.auth import (
    admin_required
)

from app.schemas.departments import (
    DepartmentCreate,
    DepartmentResponse
)
from app.services.departments import (
    get_departments_by_client
)

router = APIRouter(
    prefix="/clients",
    tags=["Clients"]
)


@router.post(
    "/create",
    response_model=ClientResponse
)
def create_new_client(
    client: ClientCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(admin_required)
):
    return create_client(
        db,
        client,
        current_admin["id"]
    )




@router.get(
    "/deactivated",
    response_model=list[ClientResponse]
)
def fetch_deactivated_clients(
    db: Session = Depends(get_db),
    current_admin=Depends(admin_required)
):
    return get_deactivated_clients(db)



@router.patch(
    "/{client_id}/restore",
    response_model=ClientResponse
)
def restore_client(
    client_id: str,
    db: Session = Depends(get_db),
    current_admin=Depends(admin_required)
):

    client = reactivate_client(
        db,
        client_id
    )

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    return client



@router.get(
    "",
    response_model=list[ClientResponse]
)
def fetch_all_clients(
    db: Session = Depends(get_db),
    current_admin=Depends(admin_required)
):
    return get_all_clients(db)


@router.get(
    "/{client_id}",
    response_model=ClientResponse
)
def fetch_client_by_id(
    client_id: str,
    db: Session = Depends(get_db),
    current_admin=Depends(admin_required)
):
    
    client = get_client_by_id(
        db,
        client_id
    )

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    return client


@router.patch(
    "/{client_id}",
    response_model=ClientResponse
)
def update_existing_client(
    client_id: str,
    client_data: ClientUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(admin_required)
):
    client = update_client(
        db,
        client_id,
        client_data
    )

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    return client







@router.delete(
    "/{client_id}"
)
def deactivate_client(
    client_id: str,
    db: Session = Depends(get_db),
    current_admin=Depends(admin_required)
):

    client = delete_client(
        db,
        client_id
    )

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    return {
        "message": "Client deactivated successfully"
    }






@router.get(
    "/{client_id}/departments",
    response_model=list[DepartmentResponse]
)
def get_client_departments(
    client_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    if (
        current_user["role"]
        == "CLIENT_ADMIN"
    ):

        if (
            current_user["client_id"]
            != client_id
        ):

            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

    return get_departments_by_client(
        db,
        client_id
    )




def fetch_subscription_status(
    client_id: str,
    db: Session = Depends(get_db)
):

    return get_client_subscription_status(
        db,
        client_id
    )
@router.get(
    "/{client_id}/subscriptions/services"
)
def fetch_subscription_services(
    client_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return get_subscription_services(
        db,
        client_id,
        current_user
    )