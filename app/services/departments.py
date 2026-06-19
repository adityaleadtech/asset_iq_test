import uuid
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.departments import Department
from app.models.clients import Client
from app.models.users import User
from app.models.subscription import Subscription


# ============ HELPER FUNCTIONS ============

def validate_department_limit(
    db: Session,
    client_id: str
):
    """
    Validate that department limit hasn't been exceeded
    """
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


def validate_manager(
    db: Session,
    manager_id: str,
    client_id: str
):
    """
    Validate that a user exists and is a manager
    """
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


def validate_parent_department(
    db: Session,
    parent_department_id: str,
    client_id: str
):
    """
    Validate that parent department exists and belongs to client
    """
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


# ============ CREATE FUNCTIONS ============

def create_department(
    db: Session,
    department_data,
    current_user: dict
):
    """
    Create a new department
    
    Access:
    - ADMIN: Can create for any client
    - CLIENT_ADMIN: Can create for their client
    - MANAGER: Cannot create departments
    - USER: Cannot create departments
    """
    # Check if department already exists
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

    # Create department
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
    db: Session,
    client_id: str,
    department_data
):
    """
    Create a department for a specific client (ADMIN only)
    """
    # Validate client exists
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

    # Check if department already exists
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

    # Create department
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


# ============ READ FUNCTIONS ============

def get_departments(
    db: Session,
    current_user: dict
):
    """
    Get departments based on user role
    
    ADMIN: Sees all departments across all clients
    CLIENT_ADMIN: Sees all departments for their client
    MANAGER: Sees only departments they manage
    USER: No access to departments (returns empty list)
    """
    # Platform Admin sees all departments
    if current_user["role"] == "ADMIN":
        return (
            db.query(Department)
            .filter(Department.is_active == True)
            .all()
        )
    
    # Client Admin sees all departments for their client
    if current_user["role"] == "CLIENT_ADMIN":
        return (
            db.query(Department)
            .filter(
                Department.client_id == current_user["client_id"],
                Department.is_active == True
            )
            .all()
        )
    
    # Manager sees only departments they manage
    if current_user["role"] == "MANAGER":
        return (
            db.query(Department)
            .filter(
                Department.manager_id == current_user["id"],
                Department.is_active == True
            )
            .all()
        )
    
    # USER - no access to departments
    # Return empty list instead of exposing department data
    return []


def get_departments_by_client(
    db: Session,
    client_id: str
):
    """
    Get all departments for a specific client (ADMIN only)
    """
    return (
        db.query(Department)
        .filter(
            Department.client_id == client_id,
            Department.is_active == True
        )
        .all()
    )


def get_department_by_id(
    db: Session,
    department_id: str,
    current_user: dict
):
    """
    Get a department by ID with role-based access control
    
    ADMIN: Can access any department
    CLIENT_ADMIN: Can access departments for their client
    MANAGER: Can only access departments they manage
    USER: No access (403 Forbidden)
    """
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

    # ADMIN - can access any department
    if current_user["role"] == "ADMIN":
        return department
    
    # CLIENT_ADMIN - can access departments for their client
    if current_user["role"] == "CLIENT_ADMIN":
        if department.client_id != current_user["client_id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )
        return department
    
    # MANAGER - can only access departments they manage
    if current_user["role"] == "MANAGER":
        if department.manager_id != current_user["id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied. You do not manage this department"
            )
        return department
    
    # USER - no access to departments
    raise HTTPException(
        status_code=403,
        detail="Access denied. Users cannot view department details"
    )


def get_deactivated_departments_by_client(
    db: Session,
    client_id: str
):
    """
    Get all deactivated departments for a client (ADMIN only)
    """
    return (
        db.query(Department)
        .filter(
            Department.client_id == client_id,
            Department.is_active == False
        )
        .all()
    )


def get_department_manager(
    db: Session,
    department_id: str,
    current_user: dict
):
    """
    Get the manager of a department with RBAC
    
    ADMIN: Can access any department manager
    CLIENT_ADMIN: Can access managers for their client
    MANAGER: Can only access managers of departments they manage
    USER: No access (403 Forbidden)
    """
    # First, validate access to the department
    department = get_department_by_id(
        db,
        department_id,
        current_user
    )
    
    # If we got here, access is granted
    if not department.manager_id:
        raise HTTPException(
            status_code=404,
            detail="No manager assigned to this department"
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


# ============ UPDATE FUNCTIONS ============

def update_department(
    db: Session,
    department_id: str,
    department_data,
    current_user: dict
):
    """
    Update a department with role-based access control
    
    ADMIN: Can update any department
    CLIENT_ADMIN: Can update departments for their client
    MANAGER: CANNOT update departments (403 Forbidden)
    USER: CANNOT update departments (403 Forbidden)
    """
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

    # Only ADMIN and CLIENT_ADMIN can update departments
    if current_user["role"] == "ADMIN":
        pass  # Allow
    
    elif current_user["role"] == "CLIENT_ADMIN":
        if department.client_id != current_user["client_id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )
    
    elif current_user["role"] == "MANAGER":
        # Managers CANNOT update departments
        raise HTTPException(
            status_code=403,
            detail="Managers cannot update departments. Only ADMIN or CLIENT_ADMIN can modify department structure."
        )
    
    else:  # USER or unknown role
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    update_data = department_data.model_dump(
        exclude_unset=True
    )
    
    # Validate manager if being updated
    if "manager_id" in update_data:
        # Only ADMIN and CLIENT_ADMIN can change manager
        if current_user["role"] not in ["ADMIN", "CLIENT_ADMIN"]:
            raise HTTPException(
                status_code=403,
                detail="Only ADMIN or CLIENT_ADMIN can change department manager"
            )
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


# ============ DELETE/DEACTIVATE FUNCTIONS ============

def deactivate_department(
    db: Session,
    department_id: str,
    current_user: dict
):
    """
    Deactivate a department (soft delete)
    
    Only ADMIN and CLIENT_ADMIN can deactivate departments
    MANAGER and USER cannot deactivate departments
    """
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

    # Only ADMIN or CLIENT_ADMIN can deactivate departments
    if current_user["role"] not in ["ADMIN", "CLIENT_ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Only ADMIN or CLIENT_ADMIN can deactivate departments"
        )

    if current_user["role"] != "ADMIN":
        if department.client_id != current_user["client_id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

    department.is_active = False
    db.commit()
    db.refresh(department)

    return department


def restore_department(
    db: Session,
    department_id: str,
    current_user: dict
):
    """
    Restore a deactivated department
    
    Only ADMIN and CLIENT_ADMIN can restore departments
    MANAGER and USER cannot restore departments
    """
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

    # Only ADMIN or CLIENT_ADMIN can restore departments
    if current_user["role"] not in ["ADMIN", "CLIENT_ADMIN"]:
        raise HTTPException(
            status_code=403,
            detail="Only ADMIN or CLIENT_ADMIN can restore departments"
        )

    if current_user["role"] != "ADMIN":
        if department.client_id != current_user["client_id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
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