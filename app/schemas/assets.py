from datetime import date

from pydantic import BaseModel


class AssetCreate(
    BaseModel
):

    category_id: str

    type_id: str

    department_id: str

    name: str

    description: str | None = None

    serial_number: str | None = None

    model: str | None = None

    manufacturer: str | None = None

    purchase_date: date | None = None

    purchase_value: float | None = None

    assigned_to_user_id: str | None = None



class AssetUpdate(
    BaseModel
):

    category_id: str | None = None

    type_id: str | None = None

    department_id: str | None = None

    name: str | None = None

    description: str | None = None

    serial_number: str | None = None

    model: str | None = None

    manufacturer: str | None = None

    purchase_date: date | None = None

    purchase_value: float | None = None

    assigned_to_user_id: str | None = None

    status: str | None = None


class AssetResponse(
    BaseModel
):

    id: str

    client_id: str

    category_id: str | None

    type_id: str | None

    department_id: str | None

    assigned_to_user_id: str | None

    name: str

    description: str | None

    serial_number: str | None

    model: str | None

    manufacturer: str | None

    purchase_date: date | None

    purchase_value: float | None

    status: str

    is_active: bool

    class Config:

        from_attributes = True



from pydantic import BaseModel


class AssetAssignRequest(BaseModel):
    user_id: str

    