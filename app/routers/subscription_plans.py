from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.config.dependencies import get_db

from app.schemas.subscription_plans import (
    SubscriptionPlanCreate,
    SubscriptionPlanResponse,
    SubscriptionPlanUpdate
)

from app.services.subscription_plans import (
    create_subscription_plan,
    deactivate_subscription_plan
)

from app.utils.auth import (
    admin_required
)

from app.services.subscription_plans import (
    create_subscription_plan,
    get_all_subscription_plans,
    get_subscription_plan_by_id,
    update_subscription_plan
)


from app.services.subscription_plans import (
    create_subscription_plan,
    get_all_subscription_plans
)

router = APIRouter(
    prefix="/subscription-plans",
    tags=["Subscription Plans"]
)


@router.post(
    "",
    response_model=SubscriptionPlanResponse
)
def create_plan(
    plan: SubscriptionPlanCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(
        admin_required
    )
):

    return create_subscription_plan(
        db,
        plan
    )




# get all subscription plans

@router.get(
    "",
    response_model=list[
        SubscriptionPlanResponse
    ]
)
def fetch_subscription_plans(
    db: Session = Depends(get_db),
    current_admin=Depends(
        admin_required
    )
):

    return get_all_subscription_plans(
        db
    )


@router.get("")
@router.get(
    "/{plan_id}",
    response_model=SubscriptionPlanResponse
)
def fetch_subscription_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_admin=Depends(
        admin_required
    )
):

    return get_subscription_plan_by_id(
        db,
        plan_id
    )




@router.patch(
    "/{plan_id}",
    response_model=SubscriptionPlanResponse
)
def update_plan(
    plan_id: str,
    plan_data: SubscriptionPlanUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(
        admin_required
    )
):

    return update_subscription_plan(
        db,
        plan_id,
        plan_data
    )
@router.delete(
    "/{plan_id}"
)
def delete_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_admin=Depends(
        admin_required
    )
):

    deactivate_subscription_plan(
        db,
        plan_id
    )

    return {
        "message":
        "Subscription plan deactivated"
    }