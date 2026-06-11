from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.config.dependencies import (
    get_db,
    get_current_user
)

from app.services.permissions import (
    has_permission
)



def require_permission(
    service_code: str,
    action: str
):

    def permission_checker(

        db: Session = Depends(get_db),

        current_user=
        Depends(
            get_current_user
        )
    ):

        allowed = has_permission(
            db,
            current_user,
            service_code,
            action
        )

        if not allowed:

            raise HTTPException(
                status_code=403,
                detail=
                (
                    f"No permission "
                    f"to {action} "
                    f"{service_code}"
                )
            )

        return True

    return permission_checker