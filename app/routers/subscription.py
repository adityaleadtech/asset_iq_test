from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.config.dependencies import get_db

from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse
)

from app.services.subscription import (
    create_subscription,
    get_client_subscription,
    get_subscription_by_id,
    update_subscription,
    suspend_subscription,
    reactivate_subscription,
    cancel_subscription
)

from app.services.subscription import (
    create_subscription,
    get_client_subscription,
    get_subscription_by_id
)

from app.services.subscription import (
    create_subscription
)

from app.utils.auth import (
    admin_required
)







router = APIRouter(
    prefix="/clients",
    tags=["Subscriptions"]
)

@router.get(
    "/subscriptions/{subscription_id}",
    response_model=SubscriptionResponse
)
def fetch_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
    current_admin=Depends(
        admin_required
    )
):

    return get_subscription_by_id(
        db,
        subscription_id
    )




@router.post(
    "/{client_id}/subscriptions",
    response_model=SubscriptionResponse
)
def create_client_subscription(
    client_id: str,
    subscription: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(
        admin_required
    )
):

    return create_subscription(
        db,
        client_id,
        subscription
    )


from app.services.subscription import (
    create_subscription,
    get_client_subscription
)


@router.get(
    "/{client_id}/subscriptions",
    response_model=SubscriptionResponse
)
def fetch_client_subscription(
    client_id: str,
    db: Session = Depends(get_db),
    current_admin=Depends(
        admin_required
    )
):

    return get_client_subscription(
        db,
        client_id
    )



from app.services.subscription import (
    create_subscription,
    get_client_subscription,
    get_subscription_by_id,
    update_subscription
)

from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionUpdate
)


@router.patch(
    "/subscriptions/{subscription_id}",
    response_model=SubscriptionResponse
)
def update_existing_subscription(
    subscription_id: str,
    subscription_data: SubscriptionUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(
        admin_required
    )
):

    return update_subscription(
        db,
        subscription_id,
        subscription_data
    )

from app.services.subscription import (
    create_subscription,
    get_client_subscription,
    get_subscription_by_id,
    update_subscription,
    suspend_subscription
)
@router.patch(
    "/subscriptions/{subscription_id}/suspend",
    response_model=SubscriptionResponse
)
def suspend_existing_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
    current_admin=Depends(
        admin_required
    )
):

    return suspend_subscription(
        db,
        subscription_id
    )


from app.services.subscription import (
    create_subscription,
    get_client_subscription,
    get_subscription_by_id,
    update_subscription,
    suspend_subscription,
    reactivate_subscription
)

@router.patch(
    "/subscriptions/{subscription_id}/reactivate",
    response_model=SubscriptionResponse
)
def reactivate_existing_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
    current_admin=Depends(
        admin_required
    )
):

    return reactivate_subscription(
        db,
        subscription_id
    )


@router.delete(
    "/subscriptions/{subscription_id}"
)
def cancel_existing_subscription(
    subscription_id: str,
    db: Session = Depends(get_db),
    current_admin=Depends(
        admin_required
    )
):

    cancel_subscription(
        db,
        subscription_id
    )

    return {
        "message":
        "Subscription cancelled successfully"
    }