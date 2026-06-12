import uuid

from fastapi import HTTPException

from app.models.clients import Client
from app.models.subscription import Subscription
from app.models.subscription_service import (
    SubscriptionService
)
from app.models.service_catalogue import (
    ServiceCatalogue
)


def create_subscription(
    db,
    client_id: str,
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

    existing_subscription = (
        db.query(Subscription)
        .filter(
            Subscription.client_id == client_id,
            Subscription.status == "ACTIVE"
        )
        .first()
    )

    if existing_subscription:

        raise HTTPException(
            status_code=400,
            detail=(
                "Client already has "
                "an active subscription"
            )
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
                (
                    f"Service "
                    f"{service_id} "
                    f"not found"
                )
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


def get_client_subscription(
    db,
    client_id: str
):

    subscription = (
        db.query(
            Subscription
        )
        .filter(
            Subscription.client_id
            ==
            client_id,

            Subscription.status
            ==
            "ACTIVE"
        )
        .first()
    )

    if not subscription:

        raise HTTPException(
            status_code=404,
            detail=
            "No active subscription found"
        )

    services = (
        db.query(
            SubscriptionService,
            ServiceCatalogue
        )
        .join(
            ServiceCatalogue,
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

    return {
        "subscription": subscription,
        "services": [
            {
                "id": service.id,
                "code": service.code,
                "name": service.name
            }
            for _, service in services
        ]
    }



def get_subscription_by_id(
    db,
    subscription_id: str
):

    subscription = (
        db.query(
            Subscription
        )
        .filter(
            Subscription.id
            ==
            subscription_id
        )
        .first()
    )

    if not subscription:

        raise HTTPException(
            status_code=404,
            detail=
            "Subscription not found"
        )

    return subscription


def update_subscription(
    db,
    subscription_id: str,
    subscription_data
):

    subscription = (
        db.query(
            Subscription
        )
        .filter(
            Subscription.id
            ==
            subscription_id
        )
        .first()
    )

    if not subscription:

        raise HTTPException(
            status_code=404,
            detail=
            "Subscription not found"
        )

    update_data = (
        subscription_data.model_dump(
            exclude_unset=True
        )
    )

    if (
        "licence_count"
        in
        update_data
    ):

        if (
            update_data[
                "licence_count"
            ]
            <
            subscription.used_licences
        ):

            raise HTTPException(
                status_code=400,
                detail=
                (
                    "Licence count "
                    "cannot be less "
                    "than used licences"
                )
            )

    services = (
        update_data.pop(
            "services",
            None
        )
    )

    for key, value in (
        update_data.items()
    ):

        setattr(
            subscription,
            key,
            value
        )

    if services is not None:

        (
            db.query(
                SubscriptionService
            )
            .filter(
                SubscriptionService
                .subscription_id
                ==
                subscription.id
            )
            .delete()
        )

        for service_id in services:

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



def suspend_subscription(
    db,
    subscription_id: str
):

    subscription = (
        db.query(
            Subscription
        )
        .filter(
            Subscription.id
            ==
            subscription_id
        )
        .first()
    )

    if not subscription:

        raise HTTPException(
            status_code=404,
            detail=
            "Subscription not found"
        )

    subscription.status = "SUSPENDED"

    db.commit()

    db.refresh(subscription)

    return subscription


def reactivate_subscription(
    db,
    subscription_id: str
):

    subscription = (
        db.query(
            Subscription
        )
        .filter(
            Subscription.id
            ==
            subscription_id
        )
        .first()
    )

    if not subscription:

        raise HTTPException(
            status_code=404,
            detail=
            "Subscription not found"
        )

    subscription.status = "ACTIVE"

    db.commit()

    db.refresh(subscription)

    return subscription


def cancel_subscription(
    db,
    subscription_id: str
):

    subscription = (
        db.query(
            Subscription
        )
        .filter(
            Subscription.id
            ==
            subscription_id
        )
        .first()
    )

    if not subscription:

        raise HTTPException(
            status_code=404,
            detail=
            "Subscription not found"
        )

    subscription.status = "CANCELLED"

    db.commit()

    db.refresh(subscription)

    return subscription


def get_client_subscription_status(
    db,
    client_id: str
):

    client = (
        db.query(Client)
        .filter(
            Client.id
            ==
            client_id,

            Client.is_active
            ==
            True
        )
        .first()
    )

    if not client:

        raise HTTPException(
            status_code=404,
            detail="Client not found"
        )

    subscription = (
        db.query(
            Subscription
        )
        .filter(
            Subscription.client_id
            ==
            client_id,

            Subscription.status
            ==
            "ACTIVE"
        )
        .first()
    )

    if not subscription:

        return {

            "client_id":
            client_id,

            "subscribed":
            False,

            "subscription_id":
            None,

            "status":
            None
        }

    return {

        "client_id":
        client_id,

        "subscribed":
        True,

        "subscription_id":
        subscription.id,

        "status":
        subscription.status,

        "expires_at":
        subscription.ends_at
    }