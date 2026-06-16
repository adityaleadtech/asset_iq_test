from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.config.dependencies import get_current_user, get_db

from app.schemas.departments import DepartmentResponse
from app.schemas.manager import (
    AssignManagerRequest,
    RemoveManagerRequest
)

from app.schemas.users import UserResponse
from app.services.manager import (
    assign_manager,
    get_manager_department,
    get_manager_users,
    remove_manager,
    get_department_manager
)

from app.utils.auth import (
    service_permission_required
)

router = APIRouter(
    prefix="/manager",
    tags=["Manager"]
)



@router.post(
    "/assign",
    summary="Assign Manager To Department",
    description="""
    Assign a user as manager of a department.

    Access:
    - CLIENT_ADMIN
    - ADMIN

    Usage:

    Department Created
       ↓
    Select User
       ↓
    Assign Manager
    """
)
def assign_department_manager(
    request: AssignManagerRequest,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "DEPARTMENTS",
            "update"
        )
    )
):

    return assign_manager(
        db,
        request,
        current_user
    )




@router.post(
    "/assign",
    summary="Assign Manager To Department",
    description="""
    Assign a user as manager of a department.

    Access:
    - CLIENT_ADMIN
    - ADMIN

    Usage:

    Department Created
       ↓
    Select User
       ↓
    Assign Manager
    """
)
def assign_department_manager(
    request: AssignManagerRequest,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "DEPARTMENTS",
            "update"
        )
    )
):

    return assign_manager(
        db,
        request,
        current_user
    )




@router.post(
    "/remove",
    summary="Remove Department Manager"
)
def remove_department_manager(
    request: RemoveManagerRequest,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "DEPARTMENTS",
            "update"
        )
    )
):

    return remove_manager(
        db,
        request,
        current_user
    )



@router.get(
    "/department/{department_id}",
    summary="Fetch Department Manager"
)
def fetch_department_manager(
    department_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        service_permission_required(
            "DEPARTMENTS",
            "read"
        )
    )
):

    return get_department_manager(
        db,
        department_id,
        current_user
    )



@router.get(
    "/department",
    response_model=DepartmentResponse,
    summary="My Department",
    description="""
    Fetch the department managed by
    the currently logged in manager.

    Access:
    - MANAGER

    Usage:
    Manager Dashboard
    """
)
def fetch_my_department(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    return get_manager_department(
        db,
        current_user
    )


@router.get(
    "/users",
    response_model=list[UserResponse],
    summary="Department Users",
    description="""
    Fetch all users belonging
    to the manager's department.

    Access:
    - MANAGER

    Usage:
    Manager Dashboard
    Employee Monitoring
    Future Geofencing
    Future SOS Monitoring
    """
)
def fetch_department_users(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    return get_manager_users(
        db,
        current_user
    )