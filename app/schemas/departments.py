from pydantic import BaseModel


class DepartmentCreate(BaseModel):

    parent_department_id: str | None = None

    name: str

    code: str | None = None

    description: str | None = None

    manager_id: str | None = None

class DepartmentResponse(BaseModel):

    id: str

    client_id: str

    name: str

    code: str | None

    description: str | None

    manager_id: str | None

    is_active: bool

    model_config = {
        "from_attributes": True
    }


class DepartmentUpdate(BaseModel):

    parent_department_id: str | None = None

    name: str | None = None

    code: str | None = None

    description: str | None = None

    manager_id: str | None = None

    is_active: bool | None = None