from fastapi import HTTPException

from app.models.users import User
from app.models.departments import Department


def assign_manager(
    db,
    request,
    current_user
):

    department = (
        db.query(Department)
        .filter(
            Department.id == request.department_id,
            Department.is_active == True
        )
        .first()
    )

    if not department:
        raise HTTPException(
            status_code=404,
            detail="Department not found"
        )

    user = (
        db.query(User)
        .filter(
            User.id == request.user_id,
            User.is_active == True
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
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

        if (
            user.client_id
            !=
            current_user["client_id"]
        ):
            raise HTTPException(
                status_code=403,
                detail="User belongs to another client"
            )

    user.role = "MANAGER"

    department.manager_id = user.id

    db.commit()

    return {
        "message":
        "Manager assigned successfully"
    }



def remove_manager(
    db,
    request,
    current_user
):

    department = (
        db.query(Department)
        .filter(
            Department.id == request.department_id,
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

    return {
        "message":
        "Manager removed successfully"
    }




def get_department_manager(
    db,
    department_id,
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

    if not department.manager_id:
        raise HTTPException(
            status_code=404,
            detail="No manager assigned"
        )

    manager = (
        db.query(User)
        .filter(
            User.id == department.manager_id,
            User.is_active == True
        )
        .first()
    )

    return manager


def get_manager_department(
    db,
    current_user
):

    if current_user["role"] != "MANAGER":

        raise HTTPException(
            status_code=403,
            detail="Manager access required"
        )

    department = (
        db.query(Department)
        .filter(
            Department.manager_id == current_user["id"],
            Department.is_active == True
        )
        .first()
    )

    if not department:

        raise HTTPException(
            status_code=404,
            detail="No department assigned"
        )

    return department


from app.models.departments import Department
from app.models.users import User
from fastapi import HTTPException


def get_manager_users(
    db,
    current_user
):

    if current_user["role"] != "MANAGER":

        raise HTTPException(
            status_code=403,
            detail="Manager access required"
        )

    department = (
        db.query(Department)
        .filter(
            Department.manager_id == current_user["id"],
            Department.is_active == True
        )
        .first()
    )

    if not department:

        raise HTTPException(
            status_code=404,
            detail="No department assigned"
        )

    users = (
        db.query(User)
        .filter(
            User.department_id == department.id,
            User.is_active == True
        )
        .all()
    )

    return users