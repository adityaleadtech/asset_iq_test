from pydantic import BaseModel


class ServicePermissionCreate(
    BaseModel
):

    service_id: str

    can_create: bool = False

    can_read: bool = False

    can_update: bool = False

    can_delete: bool = False


class RolePermissionCreate(
    BaseModel
):

    permissions: list[
        ServicePermissionCreate
    ]


class RoleServicePermissionResponse(
    BaseModel
):

    id: str

    role_id: str

    service_id: str

    can_create: bool

    can_read: bool

    can_update: bool

    can_delete: bool

    model_config = {
        "from_attributes": True
    }