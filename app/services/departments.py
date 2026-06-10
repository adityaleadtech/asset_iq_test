import uuid

from fastapi import HTTPException
from app.models.departments import Department
from app.models.clients import Client
from app.models.users import User
from app.models.departments import Department

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



from app.models.departments import Department


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


from fastapi import HTTPException


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


from fastapi import HTTPException


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

from fastapi import HTTPException


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