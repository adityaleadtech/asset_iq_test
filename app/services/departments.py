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

# Helper function to validate user license limit
def validate_user_limit(
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

    if subscription.used_licences >= subscription.licence_count:
        raise HTTPException(
            status_code=400,
            detail=(
                f"User license limit reached. "
                f"Maximum allowed: "
                f"{subscription.licence_count}"
            )
        )

    return subscription


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


# ── User License Limit Functions ──────────────────────────────────────────────

def create_user_with_limit(
    db,
    user_data,
    current_user
):
    # Validate user license limit before creating
    if current_user["role"] == "ADMIN":
        if not user_data.client_id:
            raise HTTPException(status_code=400, detail="client_id is required")
        client_id = user_data.client_id
    else:
        client_id = current_user["client_id"]
    
    validate_user_limit(db, client_id)
    
    # Continue with existing user creation logic
    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    client = (
        db.query(Client)
        .filter(Client.id == client_id, Client.is_active == True)
        .first()
    )

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    user = User(
        id=str(uuid.uuid4()),
        client_id=client_id,
        department_id=user_data.department_id,
        email=user_data.email,
        password_hash=hash_password(user_data.password),  # Make sure to import hash_password
        full_name=user_data.full_name,
        phone=user_data.phone,
        employee_id=user_data.employee_id,
        role="USER",
        is_active=True,
    )

    db.add(user)
    
    # Update subscription used_licences
    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.client_id == client_id,
            Subscription.status == "ACTIVE"
        )
        .first()
    )
    
    if subscription:
        subscription.used_licences += 1
    
    db.commit()
    db.refresh(user)

    return user


def restore_user_with_limit(
    db,
    user_id: str,
    current_user
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user["role"] != "ADMIN":
        if user.client_id != current_user["client_id"]:
            raise HTTPException(status_code=403, detail="Access denied")

    # Validate user limit before restoring
    validate_user_limit(db, user.client_id)

    user.is_active = True
    
    # Update subscription used_licences
    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.client_id == user.client_id,
            Subscription.status == "ACTIVE"
        )
        .first()
    )
    
    if subscription:
        subscription.used_licences += 1
    
    db.commit()
    db.refresh(user)

    return user


def deactivate_user_with_limit(
    db,
    user_id: str,
    current_user
):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user["role"] != "ADMIN":
        if user.client_id != current_user["client_id"]:
            raise HTTPException(status_code=403, detail="Access denied")

    user.is_active = False
    
    # Update subscription used_licences
    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.client_id == user.client_id,
            Subscription.status == "ACTIVE"
        )
        .first()
    )
    
    if subscription:
        subscription.used_licences = max(0, subscription.used_licences - 1)
    
    db.commit()
    db.refresh(user)

    return user