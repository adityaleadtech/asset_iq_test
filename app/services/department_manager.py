from app.models.departments import Department
from app.models.users import User
from fastapi import HTTPException

def assign_manager_to_department(
    db,
    department_id: str,
    manager_id: str,
    current_user
):
    department = (
        db.query(Department)
        .filter(
            Department.id == department_id,
            Department.is_active == True
        )
        .first()
    )

    if not department:
        raise HTTPException(
            status_code=404,
            detail="Department not found"
        )

    manager = (
        db.query(User)
        .filter(
            User.id == manager_id,
            User.role == "MANAGER",
            User.is_active == True
        )
        .first()
    )

    if not manager:
        raise HTTPException(
            status_code=404,
            detail="Manager not found"
        )

    if current_user["role"] != "ADMIN":
        if department.client_id != current_user["client_id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )
        
        if manager.client_id != current_user["client_id"]:
            raise HTTPException(
                status_code=403,
                detail="Manager belongs to another client"
            )

    department.manager_id = manager.id
    db.commit()
    db.refresh(department)

    return department


from fastapi import HTTPException

from app.models.departments import Department


def remove_manager_from_department(
    db,
    department_id: str,
    current_user
):

    department = (
        db.query(Department)
        .filter(
            Department.id == department_id,
            Department.is_active == True
        )
        .first()
    )

    if not department:

        raise HTTPException(
            status_code=404,
            detail="Department not found"
        )

    if current_user["role"] != "ADMIN":

        if (
            department.client_id
            !=
            current_user["client_id"]
        ):

            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

    department.manager_id = None

    db.commit()

    db.refresh(department)

    return department