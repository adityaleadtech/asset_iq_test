# app/routers/tracking.py

from datetime import datetime
from typing import Optional
from enum import Enum

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.config.dependencies import (
    get_db,
    get_current_user,
)

from app.schemas.tracking import (
    StartTrackingRequest,
    StartTrackingResponse,
    TrackingUpdateRequest,
    TrackingUpdateResponse,
    StopTrackingRequest,
    StopTrackingResponse,
    TrackingAssetResponse,
    TrackingSessionResponse,
    TrackingSessionListResponse,
)

from app.services.tracking import (
    get_trackable_assets,
    start_tracking,
    update_tracking_location,
    stop_tracking,
    get_tracking_session_details,
    get_tracking_sessions,
)


# ==========================================================
# Enums
# ==========================================================

class TrackingSessionStatus(str, Enum):
    """Tracking session status values"""
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"


# ==========================================================
# Router
# ==========================================================

router = APIRouter(
    prefix="/tracking",
    tags=["Tracking"]
)


# ==========================================================
# GET /tracking/assets
# ==========================================================

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
    return get_trackable_assets(db, current_user)


# ==========================================================
# POST /tracking/start
# ==========================================================

@router.post(
    "/start",
    response_model=StartTrackingResponse,
    status_code=status.HTTP_201_CREATED,
    response_description="Tracking session created successfully.",
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
    return start_tracking(db, payload, current_user)


# ==========================================================
# POST /tracking/update
# ==========================================================

@router.post(
    "/update",
    response_model=TrackingUpdateResponse,
    summary="Update Asset GPS Location",
    description="""
Updates the live GPS location of a single tracked asset.

The mobile application should call this endpoint every few seconds
for each tracked asset.

The API will:

- Validate the tracking session is active
- Verify the asset belongs to the session
- Store the GPS point in history
- Update the asset's latest location
- Record altitude, speed, heading, and accuracy when provided

This endpoint should be called automatically by the mobile app
during active tracking.
"""
)
def update_tracking_router(
    payload: TrackingUpdateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return update_tracking_location(db, payload, current_user)


# ==========================================================
# POST /tracking/stop
# ==========================================================

@router.post(
    "/stop",
    response_model=StopTrackingResponse,
    summary="Stop Asset Tracking Session",
    description="""
Stops an active tracking session.

The API will:

- Mark the tracking session as COMPLETED
- Record the session end time
- Remove all assets from active tracking
- Mark assets as no longer being tracked

Once stopped, no further location updates can be submitted using the
same tracking session.
"""
)
def stop_tracking_router(
    payload: StopTrackingRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return stop_tracking(db, payload, current_user)


# ==========================================================
# GET /tracking/sessions
# ==========================================================

@router.get(
    "/sessions",
    response_model=TrackingSessionListResponse,
    summary="List Tracking Sessions",
    description="""
Returns a paginated list of tracking sessions.

This endpoint powers the history screen where users can browse
past and active tracking sessions.

Supports filtering by:

- Status (ACTIVE / COMPLETED)
- User who started the session
- Pagination

### Role-Based Access

**Platform Admin:**
Can view sessions for all clients.

**Client Admin:**
Can view all sessions within their client.

**Manager:**
Can view sessions belonging to their department.

**User:**
Can view their own tracking sessions only.
"""
)
def get_tracking_sessions_router(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[TrackingSessionStatus] = Query(None, description="Filter by session status"),
    user_id: Optional[str] = Query(None, description="Filter by user who started the session"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_tracking_sessions(
        db=db,
        current_user=current_user,
        page=page,
        size=size,
        status=status.value if status else None,
        user_id=user_id,
    )


# ==========================================================
# GET /tracking/sessions/{tracking_session_id}
# ==========================================================

@router.get(
    "/sessions/{tracking_session_id}",
    response_model=TrackingSessionResponse,
    summary="Get Tracking Session",
    description="""
Returns the complete tracking session with live location and path history.

This is the **primary map endpoint** that powers both:

- **Live Tracking** - Displays current location of all assets with markers
- **Route Playback** - Shows complete GPS path history as polylines

The response includes:

- Session information (status, timestamps)
- User who started the session
- For each asset:
  - Current location (latest GPS point)
  - Complete GPS path (all historical points)
  - Asset details (name, serial number, asset tag)

### Typical Flow

1. User selects a session from the list (`GET /tracking/sessions`)
2. Frontend calls this endpoint with the session ID
3. Displays all assets on map with:
   - **Markers** at current location
   - **Polylines** showing the complete path
   - **Session metadata** in the UI

### Role-Based Access

**Platform Admin:** Can access any session
**Client Admin / Manager / User:** Can only access sessions within their client
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


# ==========================================================
# REMOVED ENDPOINTS
# ==========================================================

# ❌ GET /tracking/live - REMOVED
#    Replaced by GET /tracking/sessions/{tracking_session_id}
#    which returns both live location AND path history

# ❌ GET /tracking/history/{asset_id} - REMOVED
#    History is now accessed via GET /tracking/sessions/{tracking_session_id}
#    which returns the complete path for all assets in the session