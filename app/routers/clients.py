from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.dependencies import get_db

from app.schemas.clients import (
    ClientCreate,
    ClientResponse
)

from app.services.client_services import (
    create_client
)

from app.utils.auth import (
    admin_required
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