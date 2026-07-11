from datetime import date
import uuid

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.models.clients import Client
from app.models.departments import Department
from app.models.role_service_permissions import RoleServicePermission
from app.models.roles import Role
from app.models.service_catalogue import ServiceCatalogue
from app.models.subscription import Subscription
from app.models.users import User
from app.utils.jwthandler import create_token
from app.utils.security import hash_password, verify_password
from app.models.subscription_service import SubscriptionService


# Helper function to validate user license limit
def validate_user_license_limit(
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
                f"License limit reached. "
                f"Maximum allowed: "
                f"{subscription.licence_count}"
            )
        )

    return subscription


# Helper function to validate department belongs to client
def validate_department_ownership(db, department_id: str, client_id: str):
    if not department_id:
        return None
        
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
    
    if department.client_id != client_id:
        raise HTTPException(
            status_code=400,
            detail="Department does not belong to this client"
        )
    
    return department


# ── Client Admin ──────────────────────────────────────────────────────────────

def create_client_admin(db, admin_data):
    existing_client_admin = (
        db.query(User)
        .filter(
            User.client_id == admin_data.client_id,
            User.role == "CLIENT_ADMIN",
        )
        .first()
    )

    if existing_client_admin:
        raise HTTPException(
            status_code=400,
            detail="Client Admin already exists for this client",
        )

    # Check email globally, not just within client
    existing_email = (
        db.query(User)
        .filter(User.email == admin_data.email)
        .first()
    )

    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")

    # Client Admin is free - no license consumed
    user = User(
        id=str(uuid.uuid4()),
        client_id=admin_data.client_id,
        email=admin_data.email,
        password_hash=hash_password(admin_data.password),
        full_name=admin_data.full_name,
        phone=admin_data.phone,
        role="CLIENT_ADMIN",
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def login_client_admin(
    db,
    email: str,
    password: str
):
    admin = (
        db.query(User)
        .filter(
            User.email == email,
            User.role == "CLIENT_ADMIN",
            User.is_active == True
        )
        .first()
    )

    if not admin:
        return None

    if not verify_password(password, admin.password_hash):
        return None

    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.client_id == admin.client_id,
            Subscription.status == "ACTIVE"
        )
        .first()
    )

    if not subscription:
        raise HTTPException(
            status_code=403,
            detail="Client does not have an active subscription"
        )
        
    if subscription.ends_at < date.today():
        raise HTTPException(
            status_code=403,
            detail="Subscription has expired"
        )
    
    # Check client is active
    client = (
        db.query(Client)
        .filter(
            Client.id == admin.client_id,
            Client.is_active == True
        )
        .first()
    )

    if not client:
        raise HTTPException(
            status_code=403,
            detail="Client is inactive"
        )
        
    token = create_token(
        {
            "id": admin.id,
            "client_id": admin.client_id,
            "email": admin.email,
            "role": admin.role,
        }
    )

    return token


def get_client_admin_profile(db, user_id: str):
    return (
        db.query(User)
        .filter(User.id == user_id, User.role == "CLIENT_ADMIN")
        .first()
    )


# ── Managers ──────────────────────────────────────────────────────────────────

def create_manager(db, manager_data, current_user):
    try:
        if current_user["role"] == "ADMIN":
            if not manager_data.client_id:
                raise HTTPException(status_code=400, detail="client_id is required")
            client_id = manager_data.client_id
        else:
            client_id = current_user["client_id"]

        client = (
            db.query(Client)
            .filter(Client.id == client_id, Client.is_active == True)
            .first()
        )

        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        # Validate department belongs to client
        if manager_data.department_id:
            validate_department_ownership(db, manager_data.department_id, client_id)

        # Use helper function to validate license limit
        subscription = validate_user_license_limit(db, client_id)

        existing_user = (
            db.query(User)
            .filter(User.email == manager_data.email)
            .first()
        )

        if existing_user:
            raise HTTPException(status_code=400, detail="Email already exists")

        manager = User(
            id=str(uuid.uuid4()),
            client_id=client_id,
            department_id=manager_data.department_id,
            email=manager_data.email,
            password_hash=hash_password(manager_data.password),
            full_name=manager_data.full_name,
            phone=manager_data.phone,
            role="MANAGER",
            employee_id=manager_data.employee_id,
            is_active=True,
        )

        db.add(manager)
        subscription.used_licences += 1
        db.commit()
        db.refresh(manager)

        return manager
        
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


def get_all_managers(db, current_user, client_id: str | None = None):
    # Start with base query
    query = db.query(User).filter(User.role == "MANAGER", User.is_active == True)
    
    if current_user["role"] == "ADMIN" and client_id:
        query = query.filter(User.client_id == client_id)
        return query.all()
    
    if current_user["role"] == "CLIENT_ADMIN":
        query = query.filter(User.client_id == current_user["client_id"])
        return query.all()
    
    # For other roles (like MANAGER or USER) - if they have permission
    return query.all()


def get_managers_by_client_id(db, client_id: str):
    return (
        db.query(User)
        .filter(
            User.client_id == client_id,
            User.role == "MANAGER",
            User.is_active == True,
        )
        .all()
    )


def get_manager_by_id(db, manager_id: str, current_user):
    manager = (
        db.query(User)
        .filter(User.id == manager_id, User.role == "MANAGER")
        .first()
    )

    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")

    if current_user["role"] == "CLIENT_ADMIN":
        if manager.client_id != current_user["client_id"]:
            raise HTTPException(status_code=403, detail="Access denied")

    return manager


def update_manager(db, manager_id: str, manager_data, current_user):
    try:
        manager = (
            db.query(User)
            .filter(
                User.id == manager_id,
                User.role == "MANAGER",
                User.is_active == True,
            )
            .first()
        )

        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")

        if current_user["role"] == "CLIENT_ADMIN":
            if manager.client_id != current_user["client_id"]:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Check email uniqueness
        if manager_data.email and manager_data.email != manager.email:
            existing_user = (
                db.query(User)
                .filter(User.email == manager_data.email)
                .first()
            )
            
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="Email already exists"
                )

        # Validate department belongs to client if being updated
        if manager_data.department_id and manager_data.department_id != manager.department_id:
            validate_department_ownership(db, manager_data.department_id, manager.client_id)

        for key, value in manager_data.model_dump(exclude_unset=True).items():
            setattr(manager, key, value)

        db.commit()
        db.refresh(manager)

        return manager
        
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


def deactivate_manager(db, manager_id: str, current_user):
    try:
        # Prevent self-deactivation
        if manager_id == current_user["id"]:
            raise HTTPException(
                status_code=400,
                detail="You cannot deactivate yourself"
            )
            
        manager = (
            db.query(User)
            .filter(
                User.id == manager_id,
                User.role == "MANAGER",
                User.is_active == True,
            )
            .first()
        )

        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")

        if current_user["role"] == "CLIENT_ADMIN":
            if manager.client_id != current_user["client_id"]:
                raise HTTPException(status_code=403, detail="Access denied")

        # Prevent double deactivation
        if not manager.is_active:
            raise HTTPException(
                status_code=400,
                detail="Manager already deactivated"
            )

        subscription = (
            db.query(Subscription)
            .filter(
                Subscription.client_id == manager.client_id,
                Subscription.status == "ACTIVE",
            )
            .first()
        )

        manager.is_active = False

        if subscription:
            subscription.used_licences = max(0, subscription.used_licences - 1)

        db.commit()

        return {"message": "Manager deactivated successfully"}
        
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


def get_deactivated_managers(db, current_user):
    query = db.query(User).filter(User.role == "MANAGER", User.is_active == False)

    if current_user["role"] == "CLIENT_ADMIN":
        query = query.filter(User.client_id == current_user["client_id"])

    return query.all()


def restore_manager(db, manager_id: str, current_user):
    try:
        manager = (
            db.query(User)
            .filter(
                User.id == manager_id,
                User.role == "MANAGER",
                User.is_active == False,
            )
            .first()
        )

        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")

        if current_user["role"] == "CLIENT_ADMIN":
            if manager.client_id != current_user["client_id"]:
                raise HTTPException(status_code=403, detail="Access denied")

        # Prevent double restoration
        if manager.is_active:
            raise HTTPException(
                status_code=400,
                detail="Manager already active"
            )

        # Use helper function to validate license limit
        subscription = validate_user_license_limit(db, manager.client_id)

        manager.is_active = True
        subscription.used_licences += 1
        db.commit()
        db.refresh(manager)

        return manager
        
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


# ── Users ─────────────────────────────────────────────────────────────────────

def create_user(db, user_data, current_user,client_id:str|None=None):
    try:
        existing_user = (
            db.query(User)
            .filter(User.email == user_data.email)
            .first()
        )

        if existing_user:
            raise HTTPException(status_code=400, detail="Email already exists")

        if current_user["role"] == "ADMIN":
            if not client_id:
                raise HTTPException(status_code=400, detail="client_id is required")
            client_id = client_id
        else:
            client_id = current_user["client_id"]

        client = (
            db.query(Client)
            .filter(Client.id == client_id, Client.is_active == True)
            .first()
        )

        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Validate department belongs to client
        if user_data.department_id:
            validate_department_ownership(db, user_data.department_id, client_id)
        
        # Use helper function to validate license limit
        subscription = validate_user_license_limit(db, client_id)

        allowed_service_ids = {
            row.service_id
            for row in (
                db.query(SubscriptionService)
                .filter(
                    SubscriptionService.subscription_id == subscription.id
                )
                .all()
            )
        }

        role = Role(
            id=str(uuid.uuid4()),
            client_id=client_id,
            name=user_data.role.name,
            description=user_data.role.description,
            is_active=True,
        )

        db.add(role)
        db.flush()

        for permission in user_data.role.permissions:
            # Verify service exists in catalogue
            service = (
                db.query(ServiceCatalogue)
                .filter(
                    ServiceCatalogue.id == permission.service_id,
                    ServiceCatalogue.is_active == True,
                )
                .first()
            )

            if not service:
                raise HTTPException(
                    status_code=404,
                    detail=f"Service {permission.service_id} not found",
                )

            # Verify service is in subscription
            if permission.service_id not in allowed_service_ids:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Service {permission.service_id} "
                        "is not included in subscription"
                    )
                )

            db.add(
                RoleServicePermission(
                    id=str(uuid.uuid4()),
                    role_id=role.id,
                    service_id=permission.service_id,
                    can_create=permission.can_create,
                    can_read=permission.can_read,
                    can_update=permission.can_update,
                    can_delete=permission.can_delete,
                )
            )

        user = User(
            id=str(uuid.uuid4()),
            client_id=client_id,
            department_id=user_data.department_id,
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            full_name=user_data.full_name,
            phone=user_data.phone,
            employee_id=user_data.employee_id,
            role="USER",
            custom_role_id=role.id,
            is_active=True,
        )

        db.add(user)
        
        # Increment used licenses
        subscription.used_licences += 1
        
        db.commit()
        db.refresh(user)

        return user
        
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


def get_users(db, current_user,client_id: str | None = None):
    if current_user["role"]=="ADMIN" and client_id:
        return db.query(User).filter(User.is_active == True, User.client_id == client_id).all()
    if current_user["role"] == "ADMIN":
        return db.query(User).filter(User.is_active == True).all()

    return (
        db.query(User)
        .filter(
            User.client_id == current_user["client_id"],
            User.is_active == True,
        )
        .all()
    )


def get_user_by_id(db, user_id: str, current_user):
    user = (
        db.query(User)
        .filter(User.id == user_id, User.is_active == True)
        .first()
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user["role"] != "ADMIN":
        if user.client_id != current_user["client_id"]:
            raise HTTPException(status_code=403, detail="Access denied")

    return user


def update_user(db, user_id: str, user_data, current_user):
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if current_user["role"] != "ADMIN":
            if user.client_id != current_user["client_id"]:
                raise HTTPException(status_code=403, detail="Access denied")

        # Check email uniqueness
        if user_data.email and user_data.email != user.email:
            existing_user = (
                db.query(User)
                .filter(User.email == user_data.email)
                .first()
            )
            
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="Email already exists"
                )

        # Validate department belongs to client if being updated
        if user_data.department_id and user_data.department_id != user.department_id:
            validate_department_ownership(db, user_data.department_id, user.client_id)

        for key, value in user_data.model_dump(exclude_unset=True, exclude={"role"}).items():
            setattr(user, key, value)

        if user_data.role:
            # Get subscription and allowed services
            subscription = (
                db.query(Subscription)
                .filter(
                    Subscription.client_id == user.client_id,
                    Subscription.status == "ACTIVE"
                )
                .first()
            )

            if not subscription:
                raise HTTPException(
                    status_code=400,
                    detail="No active subscription found"
                )

            allowed_service_ids = {
                row.service_id
                for row in (
                    db.query(SubscriptionService)
                    .filter(
                        SubscriptionService.subscription_id == subscription.id
                    )
                    .all()
                )
            }

            role = db.query(Role).filter(Role.id == user.custom_role_id).first()

            if role:
                role.name = user_data.role.name
                role.description = user_data.role.description

                db.query(RoleServicePermission).filter(
                    RoleServicePermission.role_id == role.id
                ).delete()

                for permission in user_data.role.permissions:
                    # Verify service exists in catalogue
                    service = (
                        db.query(ServiceCatalogue)
                        .filter(
                            ServiceCatalogue.id == permission.service_id,
                            ServiceCatalogue.is_active == True,
                        )
                        .first()
                    )

                    if not service:
                        raise HTTPException(
                            status_code=404,
                            detail=f"Service {permission.service_id} not found",
                        )

                    # Verify service is in subscription
                    if permission.service_id not in allowed_service_ids:
                        raise HTTPException(
                            status_code=400,
                            detail=(
                                f"Service {permission.service_id} "
                                "is not included in subscription"
                            )
                        )
                    
                    db.add(
                        RoleServicePermission(
                            id=str(uuid.uuid4()),
                            role_id=role.id,
                            service_id=permission.service_id,
                            can_create=permission.can_create,
                            can_read=permission.can_read,
                            can_update=permission.can_update,
                            can_delete=permission.can_delete,
                        )
                    )

        db.commit()
        db.refresh(user)

        return user
        
    except HTTPException:
        db.rollback()
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


def deactivate_user(db, user_id: str, current_user):
    try:
        # Prevent self-deactivation
        if user_id == current_user["id"]:
            raise HTTPException(
                status_code=400,
                detail="You cannot deactivate yourself"
            )
            
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if current_user["role"] != "ADMIN":
            if user.client_id != current_user["client_id"]:
                raise HTTPException(status_code=403, detail="Access denied")

        # Prevent double deactivation
        if not user.is_active:
            raise HTTPException(
                status_code=400,
                detail="User already deactivated"
            )

        user.is_active = False
        
        # Decrement used licenses
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
        
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


def restore_user(db, user_id: str, current_user):
    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if current_user["role"] != "ADMIN":
            if user.client_id != current_user["client_id"]:
                raise HTTPException(status_code=403, detail="Access denied")

        # Prevent double restoration
        if user.is_active:
            raise HTTPException(
                status_code=400,
                detail="User already active"
            )

        # Use helper function to validate license limit
        subscription = validate_user_license_limit(db, user.client_id)

        user.is_active = True
        
        # Increment used licenses
        subscription.used_licences += 1
        
        db.commit()
        db.refresh(user)

        return user
        
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


def get_deactivated_users(db, current_user):
    if current_user["role"] == "ADMIN":
        return db.query(User).filter(User.is_active == False).all()

    return (
        db.query(User)
        .filter(
            User.client_id == current_user["client_id"],
            User.is_active == False,
        )
        .all()
    )


def login_user(
    db,
    email: str,
    password: str
):
    user = (
        db.query(User)
        .filter(
            User.email == email,
            User.role.in_(["USER", "MANAGER"]),
            User.is_active == True
        )
        .first()
    )

    if not user:
        return None

    if not verify_password(
        password,
        user.password_hash
    ):
        return None
    
    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.client_id == user.client_id,
            Subscription.status == "ACTIVE"
        )
        .first()
    )

    if not subscription:
        raise HTTPException(
            status_code=403,
            detail="Subscription inactive"
        )
    
    # Check subscription expiry
    if subscription.ends_at < date.today():
        raise HTTPException(
            status_code=403,
            detail="Subscription has expired"
        )

    token = create_token(
        {
            "id": user.id,
            "client_id": user.client_id,
            "email": user.email,
            "role": user.role,
            "custom_role_id": user.custom_role_id
        }
    )
    
    return token


def get_user_profile(
    db,
    user_id: str
):
    return (
        db.query(User)
        .filter(
            User.id == user_id,
            User.is_active == True
        )
        .first()
    )


from app.models.roles import Role
from app.models.role_service_permissions import (
    RoleServicePermission
)
from app.models.service_catalogue import (
    ServiceCatalogue
)

def get_user_services(
    db,
    current_user
):
    role_id = current_user.get(
        "custom_role_id"
    )

    if not role_id:
        return []

    permissions = (
        db.query(
            RoleServicePermission,
            ServiceCatalogue
        )
        .join(
            ServiceCatalogue,
            RoleServicePermission.service_id
            ==
            ServiceCatalogue.id
        )
        .filter(
            RoleServicePermission.role_id
            ==
            role_id
        )
        .all()
    )

    result = []

    for permission, service in permissions:
        result.append(
            {
                "service_id": service.id,
                "code": service.code,
                "name": service.name,
                "description": service.description,
                "can_create": permission.can_create,
                "can_read": permission.can_read,
                "can_update": permission.can_update,
                "can_delete": permission.can_delete
            }
        )

    return result