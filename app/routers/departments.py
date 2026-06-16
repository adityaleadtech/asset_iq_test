from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.department_manager import assign_manager_to_department
from app.schemas.users import AssignManagerRequest, UserResponse
from app.services.departments import (
    create_department,
    create_department_for_client,
    get_departments,
    get_deactivated_departments_by_client,
    update_department,
    deactivate_department,
    get_department_by_id,
    restore_department,
    get_department_manager
)
from app.schemas.departments import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse
)

from app.services.department_manager import (
    assign_manager_to_department,
    remove_manager_from_department
)


from app.utils.auth import (
    department_update_required,
    department_creator_required,
    department_view_required,
    admin_required,
    department_restore_required,
    service_permission_required
)
from app.config.dependencies import get_current_user, get_db

router = APIRouter(
    prefix="/departments",
    tags=["Departments"]
)

# ============ SPECIFIC ROUTES FIRST (no path parameters) ============

@router.post(
    "",
    response_model=DepartmentResponse
)
def create_new_department(
    department: DepartmentCreate,
    db: Session = Depends(get_db),
   current_user=Depends(
    service_permission_required(
        "DEPARTMENTS",
        "create"
    )
)
):
    return create_department(db, department, current_user)


@router.get(
    "",
    response_model=list[DepartmentResponse]
)
def fetch_departments(
    db: Session = Depends(get_db),
  current_user=Depends(
    service_permission_required(
        "DEPARTMENTS",
        "read"
    )
)  # Changed from department_creator_required
):
    return get_departments(db, current_user)  # Pass current_user instead of client_id


# ============ ROUTES WITH CLIENT_ID PARAMETER (specific pattern) ============

@router.post(
    "/clients/{client_id}/departments",
    response_model=DepartmentResponse
)
def create_department_for_specific_client(
    client_id: str,
    department: DepartmentCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(admin_required)
):
    return create_department_for_client(db, client_id, department)


@router.get(
    "/clients/{client_id}/deactivated",
    response_model=list[DepartmentResponse]
)
def fetch_client_deactivated_departments(
    client_id: str,
    db: Session = Depends(get_db),
    current_admin=Depends(admin_required)
):
    return get_deactivated_departments_by_client(db, client_id)


# ============ ROUTES WITH DEPARTMENT_ID PARAMETER (comes after specific routes) ============

@router.get(
    "/{department_id}",
    response_model=DepartmentResponse
)
def fetch_department(
    department_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
    service_permission_required(
        "DEPARTMENTS",
        "read"
    )
) # Changed from department_view_required
):
    return get_department_by_id(db, department_id, current_user)


@router.patch(
    "/{department_id}",
    response_model=DepartmentResponse
)
def update_existing_department(
    department_id: str,
    department_data: DepartmentUpdate,
    db: Session = Depends(get_db),
   current_user=Depends(
    service_permission_required(
        "DEPARTMENTS",
        "update"
    )
)
):
    return update_department(db, department_id, department_data, current_user)


@router.delete(
    "/{department_id}"
)
def delete_department(
    department_id: str,
    db: Session = Depends(get_db),
   current_user=Depends(
    service_permission_required(
        "DEPARTMENTS",
        "delete"
    )
)
):
    deactivate_department(db, department_id, current_user)
    return {"message": "Department deactivated successfully"}


@router.patch(
    "/{department_id}/restore",
    response_model=DepartmentResponse
)
def restore_existing_department(
    department_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
    service_permission_required(
        "DEPARTMENTS",
        "update"
    )
)
):
    return restore_department(db, department_id, current_user)


@router.patch(
    "/{department_id}/assign-manager",
    response_model=DepartmentResponse
)
def assign_manager(
    department_id: str,
    request: AssignManagerRequest,
    db: Session = Depends(get_db),
   current_user=Depends(
    service_permission_required(
        "DEPARTMENTS",
        "update"
    )
)
):
    return assign_manager_to_department(
        db,
        department_id,
        request.manager_id,
        current_user
    )


@router.get(
    "/{department_id}/manager",
    response_model=UserResponse
)
def fetch_department_manager(
    department_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return get_department_manager(db, department_id)


@router.patch(
    "/{department_id}/remove-manager",
    response_model=DepartmentResponse
)
def remove_manager(
    department_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
    service_permission_required(
        "DEPARTMENTS",
        "update"
    )
)
):
    return remove_manager_from_department(db, department_id, current_user)

