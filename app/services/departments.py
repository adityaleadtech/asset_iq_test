import uuid
from fastapi import HTTPException
from app.models.departments import Department
from app.models.clients import Client
from app.models.users import User
from app.models.subscription import Subscription


# Helper function to validate department limit
def validate_department_limit(
    db,
    client_id: str
):
    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.client_id == client_id,
            Subscription.status == "ACTIVE"
        )
        .first()
    )

    if not subscription:
        raise HTTPException(
            status_code=400,
            detail="No active subscription found"
        )

    department_count = (
        db.query(Department)
        .filter(
            Department.client_id == client_id,
            Department.is_active == True
        )
        .count()
    )

    if department_count >= subscription.max_departments:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Department limit reached. "
                f"Maximum allowed: "
                f"{subscription.max_departments}"
            )
        )

    return subscription


# Helper function to validate manager
def validate_manager(
    db,
    manager_id: str,
    client_id: str
):
    if not manager_id:
        return None
        
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

    if manager.client_id != client_id:
        raise HTTPException(
            status_code=400,
            detail="Manager belongs to another client"
        )
    
    return manager


# Helper function to validate parent department
def validate_parent_department(
    db,
    parent_department_id: str,
    client_id: str
):
    if not parent_department_id:
        return None
        
    parent_department = (
        db.query(Department)
        .filter(
            Department.id == parent_department_id,
            Department.client_id == client_id,
            Department.is_active == True
        )
        .first()
    )

    if not parent_department:
        raise HTTPException(
            status_code=404,
            detail="Parent department not found"
        )
    
    return parent_department


def create_department(
    db,
    department_data,
    current_user
):
    existing_department = (
        db.query(Department)
        .filter(
            Department.client_id == current_user["client_id"],
            Department.name == department_data.name,
            Department.is_active == True
        )
        .first()
    )

    if existing_department:
        raise HTTPException(
            status_code=400,
            detail="Department already exists"
        )

    # Validate department limit
    validate_department_limit(
        db,
        current_user["client_id"]
    )
    
    # Validate manager if provided
    if department_data.manager_id:
        validate_manager(
            db,
            department_data.manager_id,
            current_user["client_id"]
        )
    
    # Validate parent department if provided
    if department_data.parent_department_id:
        validate_parent_department(
            db,
            department_data.parent_department_id,
            current_user["client_id"]
        )

    department = Department(
        id=str(uuid.uuid4()),
        client_id=current_user["client_id"],
        parent_department_id=department_data.parent_department_id,
        name=department_data.name,
        code=department_data.code,
        description=department_data.description,
        manager_id=department_data.manager_id,
        is_active=True
    )

    db.add(department)
    db.commit()
    db.refresh(department)

    return department


def create_department_for_client(
    db,
    client_id: str,
    department_data
):
    client = (
        db.query(Client)
        .filter(
            Client.id == client_id,
            Client.is_active == True
        )
        .first()
    )

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    existing_department = (
        db.query(Department)
        .filter(
            Department.client_id == client_id,
            Department.name == department_data.name,
            Department.is_active == True
        )
        .first()
    )

    if existing_department:
        raise HTTPException(
            status_code=400,
            detail="Department already exists"
        )

    # Validate department limit
    validate_department_limit(
        db,
        client_id
    )
    
    # Validate manager if provided
    if department_data.manager_id:
        validate_manager(
            db,
            department_data.manager_id,
            client_id
        )
    
    # Validate parent department if provided
    if department_data.parent_department_id:
        validate_parent_department(
            db,
            department_data.parent_department_id,
            client_id
        )

    department = Department(
        id=str(uuid.uuid4()),
        client_id=client_id,
        parent_department_id=department_data.parent_department_id,
        name=department_data.name,
        code=department_data.code,
        description=department_data.description,
        manager_id=department_data.manager_id,
        is_active=True
    )

    db.add(department)
    db.commit()
    db.refresh(department)

    return department


def get_departments(
    db,
    current_user
):
    # Platform Admin sees all departments
    if current_user["role"] == "ADMIN":
        return (
            db.query(Department)
            .filter(Department.is_active == True)
            .all()
        )
    
    # Client Admin and Manager see only their client's departments
    return (
        db.query(Department)
        .filter(
            Department.client_id == current_user["client_id"],
            Department.is_active == True
        )
        .all()
    )


def get_departments_by_client(
    db,
    client_id: str
):
    return (
        db.query(Department)
        .filter(
            Department.client_id == client_id,
            Department.is_active == True
        )
        .all()
    )


def update_department(
    db,
    department_id: str,
    department_data,
    current_user
):
    department = (
        db.query(Department)
        .filter(
            Department.id == department_id
        )
        .first()
    )

    if not department:
        raise HTTPException(
            status_code=404,
            detail="Department not found"
        )

    if current_user["role"] != "ADMIN":
        if department.client_id != current_user["client_id"]:
            raise HTTPException(
                status_code=403,
                detail="You cannot update this department"
            )

    update_data = department_data.model_dump(
        exclude_unset=True
    )
    
    # Validate manager if being updated
    if "manager_id" in update_data:
        validate_manager(
            db,
            update_data["manager_id"],
            department.client_id
        )
    
    # Validate parent department if being updated
    if "parent_department_id" in update_data:
        if update_data["parent_department_id"]:
            validate_parent_department(
                db,
                update_data["parent_department_id"],
                department.client_id
            )

    for key, value in update_data.items():
        setattr(
            department,
            key,
            value
        )

    db.commit()
    db.refresh(department)

    return department


def deactivate_department(
    db,
    department_id: str,
    current_user
):
    department = (
        db.query(Department)
        .filter(
            Department.id == department_id
        )
        .first()
    )

    if not department:
        raise HTTPException(
            status_code=404,
            detail="Department not found"
        )

    if current_user["role"] != "ADMIN":
        if department.client_id != current_user["client_id"]:
            raise HTTPException(
                status_code=403,
                detail="You cannot deactivate this department"
            )

    department.is_active = False
    db.commit()
    db.refresh(department)

    return department


def get_department_by_id(
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
        if department.client_id != current_user["client_id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

    return department


def get_deactivated_departments_by_client(
    db,
    client_id: str
):
    return (
        db.query(Department)
        .filter(
            Department.client_id == client_id,
            Department.is_active == False
        )
        .all()
    )


def restore_department(
    db,
    department_id: str,
    current_user
):
    department = (
        db.query(Department)
        .filter(
            Department.id == department_id
        )
        .first()
    )

    if not department:
        raise HTTPException(
            status_code=404,
            detail="Department not found"
        )

    if current_user["role"] != "ADMIN":
        if department.client_id != current_user["client_id"]:
            raise HTTPException(
                status_code=403,
                detail="You cannot restore this department"
            )

    # Validate department limit before restoring
    validate_department_limit(
        db,
        department.client_id
    )

    department.is_active = True
    db.commit()
    db.refresh(department)

    return department


def get_department_manager(
    db,
    department_id: str
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

    if not department.manager_id:
        raise HTTPException(
            status_code=404,
            detail="No manager assigned"
        )

    manager = (
        db.query(User)
        .filter(
            User.id == department.manager_id,
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

    return manager