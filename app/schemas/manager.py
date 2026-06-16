from pydantic import BaseModel


class AssignManagerRequest(
    BaseModel
):
    user_id: str

    department_id: str


class RemoveManagerRequest(
    BaseModel
):
    department_id: str