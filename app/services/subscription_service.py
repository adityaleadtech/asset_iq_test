import uuid

from fastapi import HTTPException

from app.models.clients import Client

from app.models.subscription import (
    Subscription
)

from app.models.subscription_service import (
    SubscriptionService
)

from app.models.service_catalogue import (
    ServiceCatalogue
)



def create_subscription(
    db,
    client_id,
    subscription_data
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

    subscription = Subscription(

        id=str(uuid.uuid4()),

        client_id=client_id,

        licence_count=
        subscription_data.licence_count,

        used_licences=0,

        max_assets=
        subscription_data.max_assets,

        max_departments=
        subscription_data.max_departments,

        price=
        subscription_data.price,

        status="ACTIVE",

        starts_at=
        subscription_data.starts_at,

        ends_at=
        subscription_data.ends_at,

        auto_renew=
        subscription_data.auto_renew
    )

    db.add(subscription)

    db.flush()

    for service_id in (
        subscription_data.services
    ):

        service = (
            db.query(
                ServiceCatalogue
            )
            .filter(
                ServiceCatalogue.id
                ==
                service_id,

                ServiceCatalogue.is_active
                ==
                True
            )
            .first()
        )

        if not service:

            raise HTTPException(
                status_code=404,
                detail=
                f"Service {service_id} not found"
            )

        db.add(
            SubscriptionService(

                id=str(
                    uuid.uuid4()
                ),

                subscription_id=
                subscription.id,

                service_id=
                service_id
            )
        )

    db.commit()

    db.refresh(subscription)

    return subscription