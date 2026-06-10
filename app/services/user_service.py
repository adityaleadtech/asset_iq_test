import uuid

from fastapi import HTTPException

from app.models.users import User
from app.utils.security import hash_password


from app.models.subscription import Subscription

import uuid

from app.models.users import User

from app.utils.security import (
    hash_password
)
from fastapi import HTTPException

from app.models.users import User
from app.models.clients import Client


def create_client_admin(
    db,
    admin_data
):
    existing_client_admin = (
        db.query(User)
        .filter(
            User.client_id == admin_data.client_id,
            User.role == "CLIENT_ADMIN"
        )
        .first()
    )

    if existing_client_admin:
        raise HTTPException(
            status_code=400,
            detail="Client Admin already exists for this client"
        )

    existing_email = (
        db.query(User)
        .filter(
            User.client_id == admin_data.client_id,
            User.email == admin_data.email
        )
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    user = User(
        id=str(uuid.uuid4()),
        client_id=admin_data.client_id,
        email=admin_data.email,
        password_hash=hash_password(
            admin_data.password
        ),
        full_name=admin_data.full_name,
        phone=admin_data.phone,
        role="CLIENT_ADMIN",
        is_active=True
    )

    db.add(user)

    db.commit()

    db.refresh(user)

    return user





from app.utils.security import (
    verify_password
)

from app.utils.jwthandler import (
    create_token
)


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

    if not verify_password(
        password,
        admin.password_hash
    ):
        return None

    token = create_token(
        {
            "id": admin.id,
            "client_id": admin.client_id,
            "email": admin.email,
            "role": admin.role
        }
    )

    return token



from app.models.users import User


def get_client_admin_profile(
    db,
    user_id: str
):
    return (
        db.query(User)
        .filter(
            User.id == user_id,
            User.role == "CLIENT_ADMIN"
        )
        .first()
    )

import uuid

from fastapi import HTTPException

from app.models.users import User
from app.models.clients import Client
from app.models.subscription import Subscription

from app.utils.security import hash_password

def create_manager(
    db,
    manager_data,
    current_user
):

    if current_user["role"] == "ADMIN":

        if not manager_data.client_id:

            raise HTTPException(
                status_code=400,
                detail="client_id is required"
            )

        client_id = manager_data.client_id

    else:

        client_id = current_user["client_id"]

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
    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.client_id == client_id,
            Subscription.status == "active"
        )
        .first()
    )

    if not subscription:

        raise HTTPException(
            status_code=400,
            detail="No active subscription found"
        )
    if (
        subscription.used_licences
        >=
        subscription.licence_count
    ):

        raise HTTPException(
            status_code=400,
            detail="No licenses available"
        )
    existing_user = (
        db.query(User)
        .filter(
            User.email == manager_data.email
        )
        .first()
    )

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )
    manager = User(

        id=str(uuid.uuid4()),

        client_id=client_id,

        department_id=manager_data.department_id,

        email=manager_data.email,

        password_hash=hash_password(
            manager_data.password
        ),

        full_name=manager_data.full_name,

        phone=manager_data.phone,

        role="MANAGER",

        employee_id=manager_data.employee_id,

        is_active=True
    )

    db.add(manager)
    subscription.used_licences += 1

    db.commit()

    db.refresh(manager)

    return manager


def get_managers_for_client_admin(
    db,
    current_user
):

    return (
        db.query(User)
        .filter(
            User.client_id ==
            current_user["client_id"],

            User.role == "MANAGER",

            User.is_active == True
        )
        .all()
    )



def get_all_managers(
    db,
    current_user
):

    query = (
        db.query(User)
        .filter(
            User.role == "MANAGER",
            User.is_active == True
        )
    )

    if current_user["role"] == "CLIENT_ADMIN":

        query = query.filter(
            User.client_id ==
            current_user["client_id"]
        )

    return query.all()



def get_all_managers(
    db,
    current_user
):

    query = (
        db.query(User)
        .filter(
            User.role == "MANAGER",
            User.is_active == True
        )
    )

    if current_user["role"] == "CLIENT_ADMIN":

        query = query.filter(
            User.client_id ==
            current_user["client_id"]
        )

    return query.all()



def get_managers_by_client_id(
    db,
    client_id: str
):

    return (
        db.query(User)
        .filter(
            User.client_id == client_id,

            User.role == "MANAGER",

            User.is_active == True
        )
        .all()
    )


from fastapi import HTTPException


def get_manager_by_id(
    db,
    manager_id: str,
    current_user
):

    query = (
        db.query(User)
        .filter(
            User.id == manager_id,
            User.role == "MANAGER"
        )
    )

    manager = query.first()

    if not manager:

        raise HTTPException(
            status_code=404,
            detail="Manager not found"
        )

    if current_user["role"] == "CLIENT_ADMIN":

        if (
            manager.client_id
            !=
            current_user["client_id"]
        ):

            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

    return manager



def update_manager(
    db,
    manager_id: str,
    manager_data,
    current_user
):

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

    if current_user["role"] == "CLIENT_ADMIN":

        if (
            manager.client_id
            !=
            current_user["client_id"]
        ):

            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

    update_data = (
        manager_data.model_dump(
            exclude_unset=True
        )
    )

    for key, value in update_data.items():

        setattr(
            manager,
            key,
            value
        )

    db.commit()

    db.refresh(manager)

    return manager


def deactivate_manager(
    db,
    manager_id: str,
    current_user
):

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

    if current_user["role"] == "CLIENT_ADMIN":

        if (
            manager.client_id
            !=
            current_user["client_id"]
        ):

            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.client_id ==
            manager.client_id,
            Subscription.status == "active"
        )
        .first()
    )

    manager.is_active = False

    if subscription:

        subscription.used_licences = max(
            0,
            subscription.used_licences - 1
        )

    db.commit()

    return {
        "message":
        "Manager deactivated successfully"
    }


def get_deactivated_managers(
    db,
    current_user
):

    query = (
        db.query(User)
        .filter(
            User.role == "MANAGER",
            User.is_active == False
        )
    )

    if current_user["role"] == "CLIENT_ADMIN":

        query = query.filter(
            User.client_id ==
            current_user["client_id"]
        )

    return query.all()


def restore_manager(
    db,
    manager_id: str,
    current_user
):

    manager = (
        db.query(User)
        .filter(
            User.id == manager_id,
            User.role == "MANAGER",
            User.is_active == False
        )
        .first()
    )

    if not manager:

        raise HTTPException(
            status_code=404,
            detail="Manager not found"
        )

    if current_user["role"] == "CLIENT_ADMIN":

        if (
            manager.client_id
            !=
            current_user["client_id"]
        ):

            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.client_id ==
            manager.client_id,

            Subscription.status == "active"
        )
        .first()
    )

    if not subscription:

        raise HTTPException(
            status_code=400,
            detail="No active subscription found"
        )

    if (
        subscription.used_licences
        >=
        subscription.licence_count
    ):

        raise HTTPException(
            status_code=400,
            detail="No licenses available"
        )

    manager.is_active = True

    subscription.used_licences += 1

    db.commit()

    db.refresh(manager)

    return manager

