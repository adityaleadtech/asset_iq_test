from sqlalchemy.orm import Session
from app.models.role_service_permissions import RoleServicePermission
from app.models.service_catalogue import ServiceCatalogue


def has_permission(
    db: Session,
    user: dict,
    service_code: str,
    action: str
) -> bool:
    """
    Check if a user has permission for a specific service action
    
    Permission Hierarchy:
    1. ADMIN: Full access to everything
    2. CLIENT_ADMIN: Full access within their client
    3. MANAGER: Read access to Departments, Users, and Assets (temporary)
    4. Custom Role: Permission based on role_service_permissions
    """
    
    # Platform Admin always allowed
    if user["role"] == "ADMIN":
        return True

    # Client Admin always allowed
    if user["role"] == "CLIENT_ADMIN":
        return True

    # ============================================
    # TEMPORARY MANAGER ACCESS
    # TODO: Remove this and use proper role-based
    # permissions once manager role is created
    # ============================================
    if user["role"] == "MANAGER":
        # Managers can read these services
        allowed_services = [
            "DEPARTMENTS",
            "USERS",
            "ASSET_MANAGEMENT"
        ]
        
        # Managers can perform these actions
        allowed_actions = ["read"]
        
        if (
            service_code in allowed_services
            and action in allowed_actions
        ):
            return True
        
        # Managers cannot create, update, or delete
        return False

    # Custom Role Based Permissions
    role_id = user.get("custom_role_id")
    
    if not role_id:
        return False

    # Query the permission
    permission = (
        db.query(RoleServicePermission)
        .join(
            ServiceCatalogue,
            RoleServicePermission.service_id == ServiceCatalogue.id
        )
        .filter(
            RoleServicePermission.role_id == role_id,
            ServiceCatalogue.code == service_code
        )
        .first()
    )

    if not permission:
        return False

    # Map action to permission field
    action_map = {
        "create": permission.can_create,
        "read": permission.can_read,
        "update": permission.can_update,
        "delete": permission.can_delete
    }

    return action_map.get(action, False)


def has_any_permission(
    db: Session,
    user: dict,
    permissions: list[tuple[str, str]]
) -> bool:
    """
    Check if user has ANY of the listed permissions
    """
    for service_code, action in permissions:
        if has_permission(db, user, service_code, action):
            return True
    return False


def has_all_permissions(
    db: Session,
    user: dict,
    permissions: list[tuple[str, str]]
) -> bool:
    """
    Check if user has ALL of the listed permissions
    """
    for service_code, action in permissions:
        if not has_permission(db, user, service_code, action):
            return False
    return True