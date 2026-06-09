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