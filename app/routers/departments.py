from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.departments import (
    create_department,
    create_department_for_client,
    get_departments,
    get_deactivated_departments_by_client,
    update_department,
    deactivate_department,
    get_department_by_id,
    restore_department
)
from app.schemas.departments import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse
)
from app.utils.auth import (
    department_update_required,
    department_creator_required,
    department_view_required,
    admin_required,
    department_restore_required
)
from app.config.dependencies import get_db

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
    current_user=Depends(department_creator_required)
):
    return create_department(db, department, current_user)


@router.get(
    "",
    response_model=list[DepartmentResponse]
)
def fetch_departments(
    db: Session = Depends(get_db),
    current_user=Depends(department_creator_required)
):
    return get_departments(db, current_user["client_id"])


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


# MOVED THIS UP - before /{department_id} routes
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
    current_user=Depends(department_view_required)
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
    current_user=Depends(department_update_required)
):
    return update_department(db, department_id, department_data, current_user)


@router.delete(
    "/{department_id}"
)
def delete_department(
    department_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(department_update_required)
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
        department_restore_required
    )
):

    return restore_department(
        db,
        department_id,
        current_user
    )