from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.dependencies import (
    get_db
)

from app.utils.auth import (
    service_permission_required
)

from app.schemas.transfers import (
    TransferCreate,
    TransferResponse
)

from app.services.transfers import (
    create_transfer,
    get_transfers,
    get_transfer_by_id
)

router = APIRouter(
    prefix="/transfers",
    tags=["Transfers"]
)
@router.post(
    "",
    response_model=TransferResponse
)
def create_new_transfer(
    transfer_data: TransferCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "ASSET_MANAGEMENT",
            "update"
        )
    )
):
    return create_transfer(
        db,
        transfer_data,
        current_user
    )

@router.get(
    "",
    response_model=list[TransferResponse]
)
def fetch_transfers(
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "ASSET_MANAGEMENT",
            "read"
        )
    )
):
    return get_transfers(
        db,
        current_user
    )


@router.get(
    "/{transfer_id}",
    response_model=TransferResponse
)
def fetch_transfer(
    transfer_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "ASSET_MANAGEMENT",
            "read"
        )
    )
):
    return get_transfer_by_id(
        db,
        transfer_id,
        current_user
    )