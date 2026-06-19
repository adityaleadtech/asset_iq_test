from fastapi import HTTPException
from app.models.users import User
from app.models.departments import Department


def assign_manager(db, request, current_user):
    # Get department
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

    # Get user
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

    # Permission checks
    if current_user["role"] != "ADMIN":
        if department.client_id != current_user["client_id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )
        if user.client_id != current_user["client_id"]:
            raise HTTPException(
                status_code=403,
                detail="User belongs to another client"
            )

    # IMPROVEMENT #1: Prevent assigning ADMIN or CLIENT_ADMIN as manager
    if user.role in ["ADMIN", "CLIENT_ADMIN"]:
        raise HTTPException(
            status_code=400,
            detail="This user cannot be assigned as a manager"
        )

    # IMPROVEMENT #2: Prevent reassigning an existing manager
    if user.role == "MANAGER":
        raise HTTPException(
            status_code=400,
            detail="User is already a manager"
        )

    # Prevent replacing existing manager
    if department.manager_id:
        raise HTTPException(
            status_code=400,
            detail=f"{department.name} already has a manager assigned"
        )

    # Check if user already manages another department (defensive)
    existing_department = (
        db.query(Department)
        .filter(
            Department.manager_id == user.id,
            Department.is_active == True
        )
        .first()
    )
    if existing_department:
        raise HTTPException(
            status_code=400,
            detail=f"{user.full_name} already manages {existing_department.name}"
        )

    # Assign manager
    user.role = "MANAGER"
    user.department_id = department.id
    department.manager_id = user.id

    db.commit()
    db.refresh(user)
    db.refresh(department)

    return {
        "message": f"{user.full_name} assigned as manager of {department.name} successfully",
        "data": {
            "user_id": user.id,
            "department_id": department.id,
            "role": user.role
        }
    }


def remove_manager(db, request, current_user):
    # Get department
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

    # Permission checks
    if current_user["role"] != "ADMIN":
        if department.client_id != current_user["client_id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

    # Get current manager
    manager = (
        db.query(User)
        .filter(
            User.id == department.manager_id,
            User.is_active == True
        )
        .first()
    )

    # Remove manager role but preserve department membership
    if manager:
        manager.role = "USER"
        # Keep manager.department_id as-is unless business rules require clearing it

    # Clear department manager
    department.manager_id = None

    db.commit()
    if manager:
        db.refresh(manager)
    db.refresh(department)

    return {
        "message": "Manager removed successfully",
        "data": {
            "department_id": department.id,
            "previous_manager_id": manager.id if manager else None
        }
    }


def get_department_manager(db, department_id, current_user):
    # Get department
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

    # Permission checks
    if current_user["role"] != "ADMIN":
        if department.client_id != current_user["client_id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

    if not department.manager_id:
        raise HTTPException(
            status_code=404,
            detail="No manager assigned"
        )

    # Get manager with role validation
    manager = (
        db.query(User)
        .filter(
            User.id == department.manager_id,
            User.role == "MANAGER",
            User.is_active == True
        )
        .first()
    )
    
    # Orphan cleanup - if manager exists in department.manager_id but isn't a MANAGER
    if not manager:
        department.manager_id = None
        db.commit()
        db.refresh(department)
        raise HTTPException(
            status_code=404,
            detail="Manager not found or inactive"
        )

    return manager


def get_manager_department(db, current_user):
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


def get_manager_users(db, current_user):
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

    # IMPROVEMENT #3: Exclude manager from their own team view
    users = (
        db.query(User)
        .filter(
            User.department_id == department.id,
            User.id != current_user["id"],  # Exclude self
            User.is_active == True
        )
        .order_by(User.full_name)  # Optional: sort for better UX
        .all()
    )
    
    return {
        "department": {
            "id": department.id,
            "name": department.name
        },
        "total_members": len(users),
        "users": users
    }