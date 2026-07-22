import uuid
from datetime import datetime, timezone
from collections import defaultdict
from typing import List, Optional, Dict, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.asset import Asset
from app.models.tracking_session import TrackingSession          # ✅ Fixed
from app.models.tracking_session_asset import TrackingSessionAsset  # ✅ Fixed
from app.models.gps_logs import GPSLog
from app.models.users import User

from app.schemas.tracking import (
    StartTrackingRequest,
    StartTrackingResponse,
    StopTrackingRequest,
    StopTrackingResponse,
    TrackingAssetResponse,
    TrackingUpdateRequest,
    TrackingUpdateResponse,
    TrackingSessionResponse,
    TrackingSessionListResponse,
    TrackingSessionListItem,
    TrackingAssetDetails,
    TrackingPathPoint,
)

# ==========================================================
# Start Tracking
# ==========================================================

def start_tracking(
    db: Session,
    payload: StartTrackingRequest,
    current_user: Dict[str, Any]
) -> StartTrackingResponse:
    """
    Starts a tracking session for the selected assets.
    """
    # =====================================
    # Prevent Multiple Active Sessions
    # =====================================
    existing_session = (
        db.query(TrackingSession)
        .filter(
            TrackingSession.started_by == current_user["id"],
            TrackingSession.status == "ACTIVE"
        )
        .first()
    )

    if existing_session:
        raise HTTPException(
            status_code=400,
            detail="You already have an active tracking session."
        )

    # =====================================
    # Validate Assets
    # =====================================
    assets = (
        db.query(Asset)
        .filter(
            Asset.id.in_(payload.asset_ids),
            Asset.client_id == current_user["client_id"],
            Asset.is_active == True
        )
        .all()
    )

    if len(assets) != len(payload.asset_ids):
        raise HTTPException(
            status_code=404,
            detail="One or more assets were not found."
        )

    # =====================================
    # Verify Asset Assignment
    # =====================================
    for asset in assets:
        if asset.assigned_to_user_id != current_user["id"]:
            raise HTTPException(
                status_code=403,
                detail=f"You are not assigned to asset '{asset.name}'."
            )

        if asset.is_tracking:
            raise HTTPException(
                status_code=400,
                detail=f"Asset '{asset.name}' is already being tracked."
            )

    # =====================================
    # Create Tracking Session
    # =====================================
    session = TrackingSession(
        id=str(uuid.uuid4()),
        client_id=current_user["client_id"],
        started_by=current_user["id"],
        status="ACTIVE"
    )

    db.add(session)
    db.flush()

    # =====================================
    # Map Assets
    # =====================================
    for asset in assets:
        mapping = TrackingSessionAsset(
            id=str(uuid.uuid4()),
            tracking_session_id=session.id,
            asset_id=asset.id
        )

        db.add(mapping)

        asset.is_tracking = True
        asset.current_tracking_session_id = session.id

    db.commit()
    db.refresh(session)

    return StartTrackingResponse(
        tracking_session_id=session.id,
        status=session.status,
        started_at=session.started_at,
        message=f"Tracking started for {len(assets)} assets."
    )


# ==========================================================
# Update GPS Location
# ==========================================================

def update_tracking_location(
    db: Session,
    payload: TrackingUpdateRequest,
    current_user: Dict[str, Any]
) -> TrackingUpdateResponse:
    """
    Updates the live GPS location for a specific asset in the tracking session.
    """
    # =====================================
    # Validate Tracking Session
    # =====================================
    session = (
        db.query(TrackingSession)
        .filter(
            TrackingSession.id == payload.tracking_session_id,
            TrackingSession.started_by == current_user["id"],
            TrackingSession.status == "ACTIVE"
        )
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Active tracking session not found."
        )

    # =====================================
    # Validate Asset is in this Session
    # =====================================
    mapping = (
        db.query(TrackingSessionAsset)
        .filter(
            TrackingSessionAsset.tracking_session_id == payload.tracking_session_id,
            TrackingSessionAsset.asset_id == payload.asset_id
        )
        .first()
    )

    if not mapping:
        raise HTTPException(
            status_code=404,
            detail="Asset is not part of this tracking session."
        )

    # =====================================
    # Get the Asset
    # =====================================
    asset = (
        db.query(Asset)
        .filter(
            Asset.id == payload.asset_id,
            Asset.client_id == current_user["client_id"]
        )
        .first()
    )

    if not asset:
        raise HTTPException(
            status_code=404,
            detail="Asset not found."
        )

    # =====================================
    # Create GPS Log
    # =====================================
    timestamp = payload.recorded_at or datetime.now(timezone.utc)

    gps_log = GPSLog(
        id=str(uuid.uuid4()),
        tracking_session_id=session.id,
        asset_id=asset.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy=payload.accuracy,
        altitude=payload.altitude,
        speed=payload.speed,
        heading=payload.heading,
        recorded_at=timestamp
    )
    db.add(gps_log)

    # =====================================
    # Update Live Location on Asset
    # =====================================
    asset.current_latitude = payload.latitude
    asset.current_longitude = payload.longitude
    asset.last_scanned_at = timestamp

    db.commit()

    return TrackingUpdateResponse(
        message="GPS data recorded successfully.",
        tracking_session_id=session.id,
        asset_id=asset.id,
        recorded_at=timestamp
    )


# ==========================================================
# Stop Tracking
# ==========================================================

def stop_tracking(
    db: Session,
    payload: StopTrackingRequest,
    current_user: Dict[str, Any]
) -> StopTrackingResponse:
    """
    Stops an active tracking session.
    """
    # =====================================
    # Validate Session
    # =====================================
    session = (
        db.query(TrackingSession)
        .filter(
            TrackingSession.id == payload.tracking_session_id,
            TrackingSession.started_by == current_user["id"],
            TrackingSession.status == "ACTIVE"
        )
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Active tracking session not found."
        )

    # =====================================
    # Stop Session
    # =====================================
    session.status = "COMPLETED"
    session.ended_at = datetime.now(timezone.utc)

    # =====================================
    # Get Tracked Assets
    # =====================================
    tracked_assets = (
        db.query(TrackingSessionAsset)
        .filter(
            TrackingSessionAsset.tracking_session_id == session.id
        )
        .all()
    )

    asset_ids = [
        tracked.asset_id
        for tracked in tracked_assets
    ]

    if asset_ids:
        assets = (
            db.query(Asset)
            .filter(
                Asset.id.in_(asset_ids)
            )
            .all()
        )

        for asset in assets:
            asset.is_tracking = False
            asset.current_tracking_session_id = None

    db.commit()

    return StopTrackingResponse(
        message="Tracking stopped successfully.",
        tracking_session_id=session.id,
        ended_at=session.ended_at
    )


# ==========================================================
# Get Trackable Assets
# ==========================================================

def get_trackable_assets(
    db: Session,
    current_user: Dict[str, Any]
) -> List[TrackingAssetResponse]:
    """
    Returns assets available for tracking.
    """
    role = current_user["role"]

    # =====================================
    # USER
    # =====================================
    if role == "USER":
        assets = (
            db.query(Asset)
            .filter(
                Asset.client_id == current_user["client_id"],
                Asset.assigned_to_user_id == current_user["id"],
                Asset.is_active == True
            )
            .all()
        )

    # =====================================
    # MANAGER
    # =====================================
    elif role == "MANAGER":
        assets = (
            db.query(Asset)
            .filter(
                Asset.client_id == current_user["client_id"],
                Asset.department_id == current_user["department_id"],
                Asset.is_active == True
            )
            .all()
        )

    # =====================================
    # CLIENT ADMIN
    # =====================================
    elif role == "CLIENT_ADMIN":
        assets = (
            db.query(Asset)
            .filter(
                Asset.client_id == current_user["client_id"],
                Asset.is_active == True
            )
            .all()
        )

    # =====================================
    # PLATFORM ADMIN
    # =====================================
    else:
        assets = (
            db.query(Asset)
            .filter(
                Asset.is_active == True
            )
            .all()
        )

    return [
        TrackingAssetResponse(
            asset_id=asset.id,
            asset_name=asset.name,
            serial_number=asset.serial_number,
            asset_tag=getattr(asset, "asset_tag", None),
        )
        for asset in assets
    ]


# ==========================================================
# Get Session Details (Live + Path) - SINGLE API
# ==========================================================

def get_tracking_session_details(
    db: Session,
    tracking_session_id: str,
    current_user: Dict[str, Any]
) -> TrackingSessionResponse:
    """
    Get detailed session information with live location and path history.
    This is the SINGLE API for both live tracking and historical path.
    """
    # =====================================
    # Get Session
    # =====================================
    session = (
        db.query(TrackingSession)
        .filter(
            TrackingSession.id == tracking_session_id
        )
        .first()
    )

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Tracking session not found."
        )

    # Platform Admin can view everything
    if current_user["role"] != "ADMIN":
        if session.client_id != current_user["client_id"]:
            raise HTTPException(
                status_code=403,
                detail="Access denied."
            )

    # =====================================
    # Get User who started the session
    # =====================================
    user = (
        db.query(User)
        .filter(
            User.id == session.started_by
        )
        .first()
    )

    # =====================================
    # Get Assets in this session with their GPS logs
    # =====================================
    mappings = (
        db.query(
            TrackingSessionAsset,
            Asset
        )
        .join(
            Asset,
            Asset.id == TrackingSessionAsset.asset_id
        )
        .filter(
            TrackingSessionAsset.tracking_session_id == tracking_session_id
        )
        .all()
    )

    # =====================================
    # Get all GPS logs for this session
    # =====================================
    gps_logs = (
        db.query(GPSLog)
        .filter(
            GPSLog.tracking_session_id == tracking_session_id
        )
        .order_by(
            GPSLog.recorded_at.asc()
        )
        .all()
    )

    # =====================================
    # Group GPS logs by asset
    # =====================================
    gps_map = defaultdict(list)
    for log in gps_logs:
        gps_map[log.asset_id].append(log)

    # =====================================
    # Build Asset Details with Path
    # =====================================
    asset_details = []

    for mapping, asset in mappings:
        asset_gps = gps_map.get(asset.id, [])
        
        # Latest GPS for current location
        latest_gps = asset_gps[-1] if asset_gps else None

        # Build path
        path_points = [
            TrackingPathPoint(
                latitude=log.latitude,
                longitude=log.longitude,
                recorded_at=log.recorded_at
            )
            for log in asset_gps
        ]

        asset_details.append(
            TrackingAssetDetails(
                asset_id=asset.id,
                asset_name=asset.name,
                serial_number=asset.serial_number,
                asset_tag=getattr(asset, "asset_tag", None),
                current_latitude=latest_gps.latitude if latest_gps else None,
                current_longitude=latest_gps.longitude if latest_gps else None,
                last_updated=latest_gps.recorded_at if latest_gps else None,
                path=path_points
            )
        )

    # =====================================
    # Build Response
    # =====================================
    return TrackingSessionResponse(
        tracking_session_id=session.id,
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        tracked_by_user_id=user.id,
        tracked_by_name=user.full_name,
        assets=asset_details
    )


# ==========================================================
# Get Tracking Sessions List
# ==========================================================

def get_tracking_sessions(
    db: Session,
    current_user: Dict[str, Any],
    page: int = 1,
    size: int = 20,
    status: Optional[str] = None,
    user_id: Optional[str] = None,
) -> TrackingSessionListResponse:
    """
    Get paginated list of tracking sessions with filters.
    """
    query = (
        db.query(
            TrackingSession,
            User
        )
        .join(
            User,
            User.id == TrackingSession.started_by
        )
    )

    # =====================================
    # Client Restriction
    # =====================================
    if current_user["role"] != "ADMIN":
        query = query.filter(
            TrackingSession.client_id == current_user["client_id"]
        )

    # =====================================
    # Filters
    # =====================================
    if status:
        query = query.filter(
            TrackingSession.status == status
        )

    if user_id:
        query = query.filter(
            TrackingSession.started_by == user_id
        )

    total = query.count()

    rows = (
        query
        .order_by(
            TrackingSession.started_at.desc()
        )
        .offset(
            (page - 1) * size
        )
        .limit(size)
        .all()
    )

    items = []

    for session, user in rows:
        tracked_assets = (
            db.query(TrackingSessionAsset)
            .filter(
                TrackingSessionAsset.tracking_session_id == session.id
            )
            .count()
        )

        items.append(
            TrackingSessionListItem(
                tracking_session_id=session.id,
                tracked_by_user_id=user.id,
                tracked_by_name=user.full_name,
                status=session.status,
                started_at=session.started_at,
                ended_at=session.ended_at,
                tracked_assets=tracked_assets
            )
        )

    return TrackingSessionListResponse(
        total=total,
        page=page,
        size=size,
        items=items
    )