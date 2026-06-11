import uuid

from fastapi import HTTPException

from app.models.clients import Client
from app.models.subscription import Subscription
from app.models.subscription_plans import SubscriptionPlan



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

    plan = (
        db.query(SubscriptionPlan)
        .filter(
            SubscriptionPlan.id == subscription_data.plan_id
        )
        .first()
    )

    if not plan:

        raise HTTPException(
            status_code=404,
            detail="Subscription plan not found"
        )

    existing_subscription = (
        db.query(Subscription)
        .filter(
            Subscription.client_id == client_id,
            Subscription.status == "active"
        )
        .first()
    )

    if existing_subscription:

        raise HTTPException(
            status_code=400,
            detail="Client already has an active subscription"
        )

    subscription = Subscription(
        id=str(uuid.uuid4()),

        client_id=client_id,

        plan_id=subscription_data.plan_id,

        status="active",

        licence_count=subscription_data.licence_count,

        used_licences=0,

        billing_cycle=subscription_data.billing_cycle,

        starts_at=subscription_data.starts_at,

        ends_at=subscription_data.ends_at,

        auto_renew=subscription_data.auto_renew
    )

    db.add(subscription)

    db.commit()

    db.refresh(subscription)

    return subscription


from fastapi import HTTPException


def get_client_subscription(
    db,
    client_id: str
):

    subscription = (
        db.query(
            Subscription
        )
        .filter(
            Subscription.client_id == client_id,
            Subscription.status == "active"
        )
        .first()
    )

    if not subscription:

        raise HTTPException(
            status_code=404,
            detail="No active subscription found"
        )

    return subscription



def get_subscription_by_id(
    db,
    subscription_id: str
):

    subscription = (
        db.query(
            Subscription
        )
        .filter(
            Subscription.id == subscription_id
        )
        .first()
    )

    if not subscription:

        raise HTTPException(
            status_code=404,
            detail="Subscription not found"
        )

    return subscription


def update_subscription(
    db,
    subscription_id: str,
    subscription_data
):

    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.id == subscription_id
        )
        .first()
    )

    if not subscription:

        raise HTTPException(
            status_code=404,
            detail="Subscription not found"
        )

    update_data = (
        subscription_data.model_dump(
            exclude_unset=True
        )
    )

    if "licence_count" in update_data:

        if (
            update_data["licence_count"]
            < subscription.used_licences
        ):

            raise HTTPException(
                status_code=400,
                detail=(
                    "Licence count cannot be "
                    "less than used licences"
                )
            )

    for key, value in update_data.items():

        setattr(
            subscription,
            key,
            value
        )

    db.commit()

    db.refresh(subscription)

    return subscription



def suspend_subscription(
    db,
    subscription_id: str
):

    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.id == subscription_id
        )
        .first()
    )

    if not subscription:

        raise HTTPException(
            status_code=404,
            detail="Subscription not found"
        )

    subscription.status = "suspended"

    db.commit()

    db.refresh(subscription)

    return subscription


def reactivate_subscription(
    db,
    subscription_id: str
):

    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.id == subscription_id
        )
        .first()
    )

    if not subscription:

        raise HTTPException(
            status_code=404,
            detail="Subscription not found"
        )

    subscription.status = "active"

    db.commit()

    db.refresh(subscription)

    return subscription


def cancel_subscription(
    db,
    subscription_id: str
):

    subscription = (
        db.query(Subscription)
        .filter(
            Subscription.id == subscription_id
        )
        .first()
    )

    if not subscription:

        raise HTTPException(
            status_code=404,
            detail="Subscription not found"
        )

    subscription.status = "cancelled"

    db.commit()

    db.refresh(subscription)

    return subscription



from fastapi import HTTPException

from app.models.clients import Client
from app.models.subscription import Subscription
from app.models.subscription_plans import (
    SubscriptionPlan
)


def get_client_subscription_status(
    db,
    client_id: str
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

    subscription = (
        db.query(Subscription)
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
            "client_id": client_id,
            "subscribed": False,
            "subscription_id": None,
            "plan_name": None,
            "status": None
        }

    plan = (
        db.query(SubscriptionPlan)
        .filter(
            SubscriptionPlan.id
            ==
            subscription.plan_id
        )
        .first()
    )

    return {

        "client_id": client_id,

        "subscribed": True,

        "subscription_id":
        subscription.id,

        "plan_name":
        plan.name if plan else None,

        "status":
        subscription.status,

        "expires_at":
        subscription.end_date
    }