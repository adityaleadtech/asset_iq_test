from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config.dependencies import (
    get_db,
    get_current_user,
)

from app.schemas.tracking import (
    LiveTrackingResponse,
    StartTrackingRequest,
    TrackingAssetResponse,
    TrackingHistoryResponse,
    TrackingSessionDetailsResponse,
    TrackingSessionListResponse,
    TrackingUpdateRequest,
    StopTrackingRequest,
)
from app.services.tracking import (
    get_live_tracking_assets,
    get_trackable_assets,
    get_tracking_history,
    get_tracking_session_details,
    get_tracking_sessions,
    start_tracking,
    update_tracking_location,
    stop_tracking,
)

router = APIRouter(
    prefix="/tracking",
    tags=["Tracking"]
)


@router.get(
    "/assets",
    response_model=list[TrackingAssetResponse],
    summary="Get Trackable Assets",
    description="""
Returns all assets that the authenticated user is allowed to track.

### USER
- Returns only assets assigned to the logged-in user.

### MANAGER
- Returns all assets belonging to the manager's department.

### CLIENT_ADMIN
- Returns all assets within the client.

### ADMIN
- Returns all assets across all clients.

This endpoint is used by the mobile application to display the list of
available assets before starting a tracking session.
"""
)
def get_tracking_assets_router(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return get_trackable_assets(
        db,
        current_user
    )


@router.post(
    "/start",
    summary="Start Asset Tracking Session",
    description="""
Starts a new tracking session for one or more selected assets.

The mobile application first retrieves the list of available assets,
allows the user to select multiple assets, and then calls this endpoint.

The API will:

- Create a new tracking session.
- Associate all selected assets with that session.
- Mark the selected assets as currently being tracked.
- Prevent tracking assets that are already being tracked.
- Prevent users from creating multiple active tracking sessions.

The returned `tracking_session_id` must be used for all subsequent
tracking update requests.
"""
)
def start_tracking_router(
    payload: StartTrackingRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return start_tracking(
        db,
        payload,
        current_user,
    )


@router.post(
    "/update",
    summary="Update Live Asset Location",
    description="""
Updates the live GPS location of every asset associated with an active
tracking session.

This endpoint is intended to be called automatically by the mobile
application while tracking is active.

Recommended update interval:
- Every 2–5 seconds.

The API will:

- Validate the tracking session.
- Store GPS history.
- Update the latest latitude and longitude of every tracked asset.
- Update the asset's last scanned timestamp.

This endpoint should not be called manually by users.
"""
)
def update_tracking_router(
    payload: TrackingUpdateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_tracking_location(
        db,
        payload,
        current_user,
    )


@router.post(
    "/stop",
    summary="Stop Asset Tracking Session",
    description="""
Stops an active tracking session.

The API will:

- Mark the tracking session as stopped.
- Record the session end time.
- Remove all selected assets from active tracking.
- Mark assets as no longer being tracked.

Once stopped, no further location updates can be submitted using the
same tracking session.
"""
)
def stop_tracking_router(
    payload: StopTrackingRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return stop_tracking(
        db,
        payload,
        current_user,
    )


@router.get(
    "/live",
    response_model=LiveTrackingResponse,
    summary="Get Live Asset Tracking",
    description="""
Returns all assets that are currently being tracked.

Each asset contains:

• Current GPS location

• Complete GPS path

• Tracking session

• Tracking user

Used by the live dashboard to render
all markers and polylines on a single map.
"""
)
def get_live_tracking_assets_router(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):

    return get_live_tracking_assets(
        db,
        current_user
    )

@router.get(
    "/session/{tracking_session_id}",
    response_model=TrackingSessionDetailsResponse,
    summary="Get Tracking Session Details",
    description="""
Returns complete information about a tracking session.

The response includes:

• Tracking session information

• User who started the session

• Session status

• Start and end time

• Every asset included in that session

This endpoint is primarily used by the web dashboard and audit screens.
"""
)
def get_tracking_session_details_router(
    tracking_session_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    return get_tracking_session_details(
        db,
        tracking_session_id,
        current_user
    )




@router.get(
    "/sessions",
    response_model=TrackingSessionListResponse,
    summary="List Tracking Sessions",
    description="""
Returns a paginated list of tracking sessions.

Supports filtering by:

• Tracking Status

• User

• Pagination

Platform Admin:
Can view sessions for all clients.

Client Admin:
Can view all sessions within their client.

Manager:
Can view sessions belonging to their client.

User:
Can view their own tracking sessions.
"""
)
def get_tracking_sessions_router(
    page: int = 1,
    size: int = 20,
    status: str | None = None,
    user_id: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    return get_tracking_sessions(
        db=db,
        current_user=current_user,
        page=page,
        size=size,
        status=status,
        user_id=user_id,
    )




@router.get(
    "/history/{asset_id}",
    response_model=TrackingHistoryResponse,
    summary="Get Asset Tracking History",
    description="""
Returns the historical GPS movement of an asset.

Supports optional filtering by:

• Start Date

• End Date

• Maximum Number of Records

Typical Uses:

• Route Playback

• Audit Reports

• Movement Analysis

• Asset Timeline

Platform Admin:
Can access every asset.

Client Admin / Manager / User:
Can access assets belonging to their client.
"""
)
def get_tracking_history_router(

    asset_id: str,

    start_date: datetime | None = None,

    end_date: datetime | None = None,

    limit: int = 1000,

    db: Session = Depends(get_db),

    current_user=Depends(get_current_user),

):

    return get_tracking_history(

        db=db,

        asset_id=asset_id,

        current_user=current_user,

        start_date=start_date,

        end_date=end_date,

        limit=limit

    )