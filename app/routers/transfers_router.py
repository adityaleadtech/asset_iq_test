from datetime import date
from enum import Enum
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.utils.auth import get_current_user
from app.enums.transfer_types import TransferType
from app.schemas.transfers_schema import (
    TransferCreate,
    TransferDetailResponse,
    TransferResponse,
    TransferListResponse,
    TransferDashboardResponse
)
from app.services.transfers_service import TransferService


# ============================================================
# 🔐 ENUMS & PERMISSION DEPENDENCY
# ============================================================

class UserRole(str, Enum):
    PLATFORM_ADMIN = "PLATFORM_ADMIN"
    CLIENT_ADMIN = "CLIENT_ADMIN"
    MANAGER = "MANAGER"
    USER = "USER"


def transfer_access(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Platform Admin, Client Admin and Manager can access transfer APIs.
    """

    allowed_roles = [
        UserRole.PLATFORM_ADMIN,
        UserRole.CLIENT_ADMIN,
        UserRole.MANAGER,
    ]

    if current_user["role"] not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform transfers."
        )

    return current_user


# ============================================================
# 📍 ROUTER
# ============================================================

router = APIRouter(
    prefix="/transfers",
    tags=["Transfers"]
)


# ============================================================
# 📌 CREATE TRANSFER
# ============================================================

@router.post(
    "",
    response_model=TransferResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Transfer",
    description="""
    Creates a new asset transfer record.

    Access: Platform Admin, Client Admin, and Manager

    The transfer can be:
    - DEPARTMENT: Transfer assets to a different department
    - LOCATION: Transfer assets to a different location
    - USER: Transfer assets to a different user
    """
)
def create_transfer(
    transfer_data: TransferCreate,
    db: Session = Depends(get_db),
    current_user=Depends(transfer_access),
):
    return TransferService.create_transfer(
        transfer_data=transfer_data,
        db=db,
        current_user=current_user,
    )


# ============================================================
# 📋 GET TRANSFERS (LIST)
# ============================================================

@router.get(
    "",
    response_model=TransferListResponse,
    summary="Get Transfers",
    description="""
    Returns a paginated list of asset transfers.

    Access: Platform Admin, Client Admin, and Manager

    Supports filtering by:
    - Search term (asset name, serial number)
    - Transfer type
    - Transferred by user
    - Date range (start_date to end_date)
    """
)
def get_transfers(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search by asset name or serial number"),
    transfer_type: TransferType | None = Query(None, description="Filter by transfer type"),
    transferred_by: UUID | None = Query(None, description="Filter by user who performed the transfer"),
    start_date: date | None = Query(None, description="Filter transfers from this date"),
    end_date: date | None = Query(None, description="Filter transfers up to this date"),
    db: Session = Depends(get_db),
    current_user=Depends(transfer_access),
):
    return TransferService.get_transfers(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
        search=search,
        transfer_type=transfer_type,
        transferred_by=transferred_by,
        start_date=start_date,
        end_date=end_date,
    )


# ============================================================
# 📈 TRANSFER DASHBOARD
# ============================================================

@router.get(
    "/dashboard",
    response_model=TransferDashboardResponse,
    summary="Transfer Dashboard",
    description="""
    Returns dashboard statistics for transfers.

    Access: Platform Admin, Client Admin, and Manager

    Includes:
    - Total transfers
    - Transfers by type (department, location, user)
    - Total assets transferred
    - Recent transfer activity
    """
)
def transfer_dashboard(
    db: Session = Depends(get_db),
    current_user=Depends(transfer_access),
):
    return TransferService.get_transfer_dashboard(
        db=db,
        current_user=current_user,
    )


# ============================================================
# 📱 MY TRANSFERS (Mobile)
# ============================================================

@router.get(
    "/my-transfers",
    response_model=list[TransferResponse],
    summary="My Transfers",
    description="""
    Returns transfers where the current user is involved.

    Access: All authenticated users

    A user is considered involved if:
    - They initiated the transfer (transferred_by), OR
    - Assets were transferred FROM them (from_user_id), OR
    - Assets were transferred TO them (to_user_id)

    This endpoint is designed for the mobile app to show
    transfers relevant to the logged-in user.
    """
)
def get_my_transfers(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return TransferService.get_my_transfers(
        db=db,
        current_user=current_user,
    )


# ============================================================
# 📄 TRANSFER REPORT (PDF)
# ============================================================

@router.get(
    "/{transfer_id}/report",
    summary="Transfer Report",
    description="""
    Generates a PDF report for a specific transfer.

    Access: Platform Admin, Client Admin, and Manager

    Returns a downloadable PDF containing:
    - Transfer details
    - Asset movement history
    - User details
    - Timestamps
    """
)
def get_transfer_report(
    transfer_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(transfer_access),
):
    return TransferService.get_transfer_report(
        transfer_id=transfer_id,
        db=db,
        current_user=current_user,
    )


# ============================================================
# 📊 GET TRANSFER DETAILS
# ============================================================

@router.get(
    "/{transfer_id}",
    response_model=TransferDetailResponse,
    summary="Get Transfer Details",
    description="""
    Returns detailed information about a specific transfer.

    Access: Platform Admin, Client Admin, and Manager

    Includes:
    - Transfer metadata
    - All assets in the transfer with their from/to details
    - Department, location, and user changes
    """
)
def get_transfer(
    transfer_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(transfer_access),
):
    return TransferService.get_transfer(
        transfer_id=transfer_id,
        db=db,
        current_user=current_user,
    )