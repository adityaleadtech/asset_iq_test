import uuid
import re
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, UploadFile

from app.models.clients import Client
from app.models.users import User
from app.models.subscription import Subscription
from app.models.subscription_service import SubscriptionService
from app.models.service_catalogue import ServiceCatalogue
from app.services.cloudinary_service import upload_image
from app.utils.security import hash_password  # FIXED: Changed from auth to security, get_password_hash to hash_password


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


def create_client(
    db: Session,
    client_data,
    admin_id: str,
    image_file: UploadFile
):
    """
    Create a new client with logo upload
    """
    # =====================================
    # Check Duplicate Client Name
    # =====================================
    existing_client = (
        db.query(Client)
        .filter(Client.name == client_data.name.strip())
        .first()
    )

    if existing_client:
        raise HTTPException(
            status_code=400,
            detail=f"Client with name '{client_data.name}' already exists"
        )

    # =====================================
    # Check Duplicate Email
    # =====================================
    existing_email = (
        db.query(Client)
        .filter(Client.contact_email == client_data.contact_email.lower().strip())
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=400,
            detail=f"Client with email '{client_data.contact_email}' already exists"
        )

    # =====================================
    # Generate Client Code
    # =====================================
    client_code = generate_unique_client_code(db, client_data.name)

    # =====================================
    # Upload Client Logo
    # =====================================
    logo_url = upload_image(
        image_file=image_file,
        folder=f"assetiq/clients/{client_code}/logo"
    )

    # =====================================
    # Build Full Address
    # =====================================
    address_parts = [
        client_data.address_line_1,
        client_data.address_line_2,
        client_data.address_line_3
    ]

    full_address = "\n".join([part for part in address_parts if part])

    # =====================================
    # Create Client Object
    # =====================================
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
        logo_url=logo_url,
        is_active=True,
        created_by_admin_id=admin_id
    )

    # =====================================
    # Save Client
    # =====================================
    try:
        db.add(client)
        db.commit()
        db.refresh(client)
        return client

    except IntegrityError as error:
        db.rollback()
        error_message = str(error)

        if "Duplicate entry" in error_message:
            if "idx_client_name" in error_message:
                raise HTTPException(
                    status_code=400,
                    detail=f"Client name '{client_data.name}' already exists"
                )
            elif "idx_client_email" in error_message:
                raise HTTPException(
                    status_code=400,
                    detail=f"Client email '{client_data.contact_email}' already exists"
                )
            elif "client_code" in error_message:
                raise HTTPException(
                    status_code=400,
                    detail="System error: Unable to generate unique client code"
                )

        raise HTTPException(
            status_code=500,
            detail="Database error occurred"
        )


def get_all_clients(db):
    """
    Get all clients
    """
    return db.query(Client).all()


def get_client_by_id(db, client_id: str):
    """
    Get a client by ID
    """
    return db.query(Client).filter(Client.id == client_id).first()


def update_client(db, client_id: str, client_data):
    """
    Update client information
    """
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        return None

    update_data = client_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(client, key, value)

    db.commit()
    db.refresh(client)

    return client


def delete_client(db, client_id: str):
    """
    Soft delete a client (set is_active to False)
    """
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        return None

    client.is_active = False
    db.commit()
    db.refresh(client)

    return client


def get_deactivated_clients(db):
    """
    Get all deactivated clients
    """
    return db.query(Client).filter(Client.is_active == False).all()


def reactivate_client(db, client_id: str):
    """
    Reactivate a deactivated client
    """
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        return None

    client.is_active = True
    db.commit()
    db.refresh(client)

    return client


def get_subscription_services(db, client_id: str, current_user):
    """
    Get all services for a client's active subscription
    """
    if current_user["role"] != "ADMIN" and current_user["client_id"] != client_id:
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
        db.query(ServiceCatalogue)
        .join(
            SubscriptionService,
            SubscriptionService.service_id == ServiceCatalogue.id
        )
        .filter(SubscriptionService.subscription_id == subscription.id)
        .all()
    )

    return services


def get_client_admin(db, client_id: str, current_user):
    """
    Get the admin for a specific client
    """
    if current_user["role"] != "ADMIN":
        if current_user["client_id"] != client_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied"
            )

    admin = (
        db.query(User)
        .filter(
            User.client_id == client_id,
            User.role == "CLIENT_ADMIN",
            User.is_active == True
        )
        .first()
    )

    if not admin:
        raise HTTPException(
            status_code=404,
            detail="Client Admin not found"
        )

    return admin


def get_client_admin_details(db, admin_id: str):
    """
    Get client admin details by ID
    """
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


def update_client_admin(db, admin_id: str, admin_data):
    """
    Update client admin information
    """
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

    update_data = admin_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(admin, key, value)

    db.commit()
    db.refresh(admin)

    return admin


def update_admin_password(db: Session, admin_id: str, new_password: str):
    """
    Update admin password
    """
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

    # Hash the new password using the correct function
    hashed_password = hash_password(new_password)  # FIXED: Changed from get_password_hash to hash_password
    admin.password_hash = hashed_password

    db.commit()
    db.refresh(admin)

    return admin


def deactivate_admin(db: Session, admin_id: str):
    """
    Deactivate admin (soft delete)
    Sets is_active = False
    """
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

    admin.is_active = False
    db.commit()
    db.refresh(admin)

    return admin


def reactivate_admin(db: Session, admin_id: str):
    """
    Reactivate admin
    Sets is_active = True
    """
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

    admin.is_active = True
    db.commit()
    db.refresh(admin)

    return admin