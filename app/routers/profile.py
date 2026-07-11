from fastapi import APIRouter,Depends
from sqlalchemy.orm import  Session

from app.config.dependencies import get_current_user, get_db
from app.services.profile import get_profile



router= APIRouter(
    prefix="/profile",
    tags=["Profile"]
)


@router.get("")
def get_profile_router(db:Session=Depends(get_db),current_user=Depends(
        get_current_user
    )):
    print("CALLED")

    return get_profile(db,current_user)


