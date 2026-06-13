import uuid

from app.models.clients import Client


import uuid
import re
from sqlalchemy.orm import Session
from app.models.clients import Client
from app.models.users import User

def generate_unique_client_code(db: Session, base_name: str) -> str:
    """
    Generate a unique client code from the client name
    Example: "Acme Corporation" -> "ACME_CORPORATION" or "ACME_CORPORATION_1"
    """
    # Convert name to code: uppercase, replace spaces with underscores, remove special chars
    base_code = re.sub(r'[^a-zA-Z0-9\s]', '', base_name)
    base_code = base_code.upper().strip()
    base_code = re.sub(r'\s+', '_', base_code)
    
    # Limit to 45 characters to leave room for suffix
    if len(base_code) > 45:
        base_code = base_code[:45]
    
    # Remove trailing underscore if exists
    base_code = base_code.rstrip('_')
    
    # Check if code exists
    existing = db.query(Client).filter(Client.client_code == base_code).first()
    if not existing:
        return base_code
    
    # If exists, add a number suffix
    counter = 1
    while True:
        new_code = f"{base_code}_{counter}"
        existing = db.query(Client).filter(Client.client_code == new_code).first()
        if not existing:
            return new_code
        counter += 1
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

def create_client(db: Session, client_data, admin_id):
    # Check for duplicate name
    existing_client = db.query(Client).filter(
        Client.name == client_data.name.strip()
    ).first()
    
    if existing_client:
        raise HTTPException(
            status_code=400,
            detail=f"Client with name '{client_data.name}' already exists"
        )
    
    # Check for duplicate email
    existing_email = db.query(Client).filter(
        Client.contact_email == client_data.contact_email.lower().strip()
    ).first()
    
    if existing_email:
        raise HTTPException(
            status_code=400,
            detail=f"Client with email '{client_data.contact_email}' already exists"
        )
    
    # Generate unique client code
    client_code = generate_unique_client_code(db, client_data.name)
    
    # Build full address
    address_parts = [
        client_data.address_line_1,
        client_data.address_line_2,
        client_data.address_line_3
    ]
    full_address = "\n".join([part for part in address_parts if part])
    
    client = Client(
        id=str(uuid.uuid4()),
        client_code=client_code,
        name=client_data.name.strip(),
        industry=client_data.industry,
        contact_email=client_data.contact_email.lower().strip(),
        contact_phone=client_data.contact_phone,
        address=full_address if full_address else None,
        address_line_1=client_data.address_line_1,
        address_line_2=client_data.address_line_2,
        address_line_3=client_data.address_line_3,
        logo_url=client_data.logo_url,
        is_active=True,
        created_by_admin_id=admin_id
    )
    
    try:
        db.add(client)
        db.commit()
        db.refresh(client)
        return client
    except IntegrityError as e:
        db.rollback()
        if "Duplicate entry" in str(e):
            if "idx_client_name" in str(e):
                raise HTTPException(400, f"Client name '{client_data.name}' already exists")
            elif "idx_client_email" in str(e):
                raise HTTPException(400, f"Client email '{client_data.contact_email}' already exists")
            elif "client_code" in str(e):
                raise HTTPException(400, "System error: Unable to generate unique client code")
        raise HTTPException(500, "Database error occurred")

# Rest of your service functions remain the same

def get_all_clients(db):
    return db.query(Client).all()





def get_client_by_id(
    db,
    client_id: str
):
    return (
        db.query(Client)
        .filter(
            Client.id == client_id
        )
        .first()
    )



def update_client(
    db,
    client_id: str,
    client_data
):
    client = (
        db.query(Client)
        .filter(
            Client.id == client_id
        )
        .first()
    )

    if not client:
        return None

    update_data = client_data.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(
            client,
            key,
            value
        )

    db.commit()

    db.refresh(client)

    return client





def delete_client(
    db,
    client_id: str
):
    client = (
        db.query(Client)
        .filter(
            Client.id == client_id
        )
        .first()
    )

    if not client:
        return None

    client.is_active = False

    db.commit()

    db.refresh(client)

    return client



def get_deactivated_clients(db):
    return (
        db.query(Client)
        .filter(
            Client.is_active == False
        )
        .all()
    )


def reactivate_client(
    db,
    client_id: str
):
    client = (
        db.query(Client)
        .filter(
            Client.id == client_id
        )
        .first()
    )

    if not client:
        return None

    client.is_active = True

    db.commit()

    db.refresh(client)

    return client



from fastapi import HTTPException

from app.models.subscription import Subscription
from app.models.subscription_service import (
    SubscriptionService
)
from app.models.service_catalogue import (
    ServiceCatalogue
)


def get_subscription_services(
    db,
    client_id: str,
    current_user
):

    if (
        current_user["role"] != "ADMIN"
        and
        current_user["client_id"] != client_id
    ):

        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

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
            status_code=404,
            detail="No active subscription found"
        )

    services = (
        db.query(
            ServiceCatalogue
        )
        .join(
            SubscriptionService,
            SubscriptionService.service_id
            ==
            ServiceCatalogue.id
        )
        .filter(
            SubscriptionService.subscription_id
            ==
            subscription.id
        )
        .all()
    )

    return services





def get_client_admin(
    db,
    client_id: str
):

    admin = (
        db.query(User)
        .filter(
            User.client_id == client_id,
            User.role == "CLIENT_ADMIN"
        )
        .first()
    )

    if not admin:
        raise HTTPException(
            status_code=404,
            detail="Client Admin not found"
        )

    return admin



def get_client_admin_details(
    db,
    admin_id: str
):

    admin = (
        db.query(User)
        .filter(
            User.id == admin_id,
            User.role == "CLIENT_ADMIN"
        )
        .first()
    )

    if not admin:
        raise HTTPException(
            status_code=404,
            detail="Client Admin not found"
        )

    return admin


def update_client_admin(
    db,
    admin_id: str,
    admin_data
):

    admin = (
        db.query(User)
        .filter(
            User.id == admin_id,
            User.role == "CLIENT_ADMIN"
        )
        .first()
    )

    if not admin:
        raise HTTPException(
            status_code=404,
            detail="Client Admin not found"
        )

    update_data = (
        admin_data.model_dump(
            exclude_unset=True
        )
    )

    for key, value in update_data.items():

        setattr(
            admin,
            key,
            value
        )

    db.commit()

    db.refresh(admin)

    return admin