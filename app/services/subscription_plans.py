import uuid

from fastapi import HTTPException

from app.models.subscription_plans import (
    SubscriptionPlan
)

import json
def create_subscription_plan(
    db,
    plan_data
):
    existing_plan = (
        db.query(SubscriptionPlan)
        .filter(
            SubscriptionPlan.name == plan_data.name
        )
        .first()
    )

    if existing_plan:
        raise HTTPException(
            status_code=400,
            detail="Subscription plan already exists"
        )

    plan = SubscriptionPlan(
        id=str(uuid.uuid4()),
        name=plan_data.name,
        # REMOVED: max_users=plan_data.max_users,
        max_assets=plan_data.max_assets,
        max_locations=plan_data.max_locations,
        price_monthly=plan_data.price_monthly,
        price_annually=plan_data.price_annually,
        features_json=json.dumps(
            plan_data.features_json
        ) if plan_data.features_json else None
    )

    db.add(plan)
    db.commit()
    db.refresh(plan)

    return plan

def get_all_subscription_plans(
    db
):
    return (
        db.query(
            SubscriptionPlan
        )
        .all()
    )


from fastapi import HTTPException


def get_subscription_plan_by_id(
    db,
    plan_id: str
):

    plan = (
        db.query(
            SubscriptionPlan
        )
        .filter(
            SubscriptionPlan.id == plan_id
        )
        .first()
    )

    if not plan:

        raise HTTPException(
            status_code=404,
            detail="Subscription plan not found"
        )

    return plan





def update_subscription_plan(
    db,
    plan_id: str,
    plan_data
):

    plan = (
        db.query(
            SubscriptionPlan
        )
        .filter(
            SubscriptionPlan.id == plan_id
        )
        .first()
    )

    if not plan:

        raise HTTPException(
            status_code=404,
            detail="Subscription plan not found"
        )

    update_data = (
        plan_data.model_dump(
            exclude_unset=True
        )
    )

    if "features_json" in update_data:

        update_data["features_json"] = json.dumps(
            update_data["features_json"]
        )

    for key, value in update_data.items():

        setattr(
            plan,
            key,
            value
        )

    db.commit()

    db.refresh(plan)

    return plan


def deactivate_subscription_plan(
    db,
    plan_id: str
):

    plan = (
        db.query(
            SubscriptionPlan
        )
        .filter(
            SubscriptionPlan.id == plan_id
        )
        .first()
    )

    if not plan:

        raise HTTPException(
            status_code=404,
            detail="Subscription plan not found"
        )

    plan.is_active = False

    db.commit()

    db.refresh(plan)

    return plan