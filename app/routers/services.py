from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.config.dependencies import (
    get_db,
    service_view_required
)

from app.services.services import (
    create_service,
    get_all_services,
    get_deactivated_services,
    get_service_by_id,
    update_service,
    deactivate_service
)

from app.services.services import (
    create_service,
    get_all_services,
    get_service_by_id,
    update_service
)

from app.schemas.services import (
    ServiceCreate,
    ServiceUpdate,
    ServiceResponse
)

from app.utils.auth import (
    admin_required
)

from app.schemas.services import (
    ServiceCreate,
    ServiceResponse
)

from app.services.services import (
    create_service,
    update_service
)

router = APIRouter(
    prefix="/services",
    tags=["Services"]
)


@router.get(
    "/deactivated",
    response_model=list[ServiceResponse]
)
def fetch_deactivated_services(
    db: Session = Depends(get_db),
    current_user=Depends(
        admin_required
    )
):

    return get_deactivated_services(db)

@router.post(
    "",
    response_model=ServiceResponse
)
def create_new_service(
    service: ServiceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        admin_required
    )
):

    return create_service(
        db,
        service
    )




from app.services.services import (
    create_service,
    get_all_services
)

@router.get(
    "",
    response_model=list[ServiceResponse]
)
def fetch_all_services(
    db: Session = Depends(get_db),
    current_user=Depends(service_view_required)
):

    return get_all_services(db)



from app.services.services import (
    create_service,
    get_all_services,
    get_service_by_id
)
@router.get(
    "/{service_id}",
    response_model=ServiceResponse
)
def fetch_service(
    service_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(service_view_required)
):

    return get_service_by_id(
        db,
        service_id
    )


@router.patch(
    "/{service_id}",
    response_model=ServiceResponse
)
def update_existing_service(
    service_id: str,
    service_data: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        admin_required
    )
):

    return update_service(
        db,
        service_id,
        service_data
    )



@router.delete(
    "/{service_id}",
    response_model=ServiceResponse
)
def delete_service(
    service_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        admin_required
    )
):

    return deactivate_service(
        db,
        service_id
    )


from app.services.services import (
    create_service,
    get_all_services,
    get_service_by_id,
    update_service,
    deactivate_service,
    restore_service
)

@router.patch(
    "/{service_id}/restore",
    response_model=ServiceResponse
)
def restore_existing_service(
    service_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        admin_required
    )
):

    return restore_service(
        db,
        service_id
    )

