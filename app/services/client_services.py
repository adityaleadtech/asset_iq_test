import uuid

from app.models.clients import Client


def create_client(
    db,
    client_data,
    admin_id
):
    client = Client(
        id=str(uuid.uuid4()),
        name=client_data.name,
        industry=client_data.industry,
        contact_email=client_data.contact_email,
        contact_phone=client_data.contact_phone,
        address=client_data.address,
        logo_url=client_data.logo_url,
        is_active=True,
        created_by_admin_id=admin_id
    )

    db.add(client)

    db.commit()

    db.refresh(client)

    return client