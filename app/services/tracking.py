import uuid
from datetime import datetime
from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.asset import Asset
from app.models.tracking_session import TrackingSession
from app.models.tracking_session_asset import TrackingSessionAsset
from app.models.gps_logs import GPSLog
from app.models.users import User  # FIXED: Using correct import path

from app.schemas.tracking import (
    StartTrackingRequest,
    StartTrackingResponse,
    StopTrackingRequest,
    StopTrackingResponse,
    TrackingUpdateRequest,
)


def start_tracking(
    db: Session,
    payload: StartTrackingRequest,
    current_user
):
    """
    Starts a tracking session for the selected assets.
    """

    # =====================================
    # Prevent Multiple Active Sessions
    # =====================================

    existing_session = (
        db.query(TrackingSession)
        .filter(
            TrackingSession.user_id == current_user["id"],
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
        user_id=current_user["id"],
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
        tracked_assets=len(assets),
        started_at=session.started_at,
        message="Tracking started successfully."
    )


def update_tracking_location(
    db: Session,
    payload: TrackingUpdateRequest,
    current_user
):
    """
    Updates the live location for every asset
    in the active tracking session.
    """

    # =====================================
    # Validate Tracking Session
    # =====================================

    session = (
        db.query(TrackingSession)
        .filter(
            TrackingSession.id == payload.tracking_session_id,
            TrackingSession.user_id == current_user["id"],
            TrackingSession.status == "ACTIVE"
        )
        .first()
    )

    if not session:

        raise HTTPException(
            status_code=404,
            detail="Tracking session not found."
        )

    # =====================================
    # Fetch Tracked Assets
    # =====================================

    tracked_assets = (
        db.query(TrackingSessionAsset)
        .filter(
            TrackingSessionAsset.tracking_session_id == session.id
        )
        .all()
    )

    # =====================================
    # Update Each Asset
    # =====================================

    for tracked_asset in tracked_assets:

        asset = (
            db.query(Asset)
            .filter(
                Asset.id == tracked_asset.asset_id
            )
            .first()
        )

        if not asset:
            continue

        # -------------------------------
        # Store GPS History
        # -------------------------------

        gps_log = GPSLog(
            id=str(uuid.uuid4()),
            tracking_session_id=session.id,
            asset_id=asset.id,
            latitude=payload.latitude,
            longitude=payload.longitude,
            accuracy=payload.accuracy,
            speed=payload.speed,
            recorded_at=payload.recorded_at
        )

        db.add(gps_log)

        # -------------------------------
        # Update Live Location
        # -------------------------------

        asset.current_latitude = payload.latitude
        asset.current_longitude = payload.longitude
        asset.last_scanned_at = payload.recorded_at

    db.commit()

    return {
        "message": "Location updated successfully."
    }


def stop_tracking(
    db: Session,
    payload: StopTrackingRequest,
    current_user
):
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
            TrackingSession.user_id == current_user["id"],
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

    session.status = "STOPPED"
    session.ended_at = datetime.utcnow()

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
        ended_at=session.ended_at
    )


def get_trackable_assets(
    db: Session,
    current_user
):
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

    return assets


def get_live_tracking_assets(
    db: Session,
    current_user
):
    """
    Get all assets currently being tracked with their GPS paths
    """

    # -------------------------------------
    # Query 1: Active Tracking Sessions + Assets
    # -------------------------------------

    query = (
        db.query(
            TrackingSession,
            TrackingSessionAsset,
            Asset,
            User
        )
        .join(
            TrackingSessionAsset,
            TrackingSession.id == TrackingSessionAsset.tracking_session_id
        )
        .join(
            Asset,
            Asset.id == TrackingSessionAsset.asset_id
        )
        .join(
            User,
            User.id == TrackingSession.user_id
        )
        .filter(
            TrackingSession.status == "ACTIVE"
        )
    )

    if current_user["role"] != "ADMIN":

        query = query.filter(
            TrackingSession.client_id == current_user["client_id"]
        )

    rows = query.all()

    if not rows:
        return {"assets": []}

    # -------------------------------------
    # Collect Active Sessions
    # -------------------------------------

    session_ids = list({
        session.id
        for session, _, _, _ in rows
    })

    # -------------------------------------
    # Query 2: Fetch all GPS logs
    # -------------------------------------

    gps_logs = (
        db.query(GPSLog)
        .filter(
            GPSLog.tracking_session_id.in_(session_ids)
        )
        .order_by(
            GPSLog.tracking_session_id,
            GPSLog.asset_id,
            GPSLog.recorded_at
        )
        .all()
    )

    # -------------------------------------
    # Group GPS logs
    # -------------------------------------

    gps_map = defaultdict(list)

    for log in gps_logs:

        gps_map[
            (
                log.tracking_session_id,
                log.asset_id
            )
        ].append({

            "latitude": log.latitude,

            "longitude": log.longitude,

            "recorded_at": log.recorded_at

        })

    # -------------------------------------
    # Build Response
    # -------------------------------------

    response = []

    for session, mapping, asset, user in rows:

        path = gps_map.get(
            (
                session.id,
                asset.id
            ),
            []
        )

        response.append({

            "tracking_session_id": session.id,

            "asset_id": asset.id,

            "asset_name": asset.name,

            "serial_number": asset.serial_number,

            "tracked_by_user_id": user.id,

            "tracked_by_name": user.full_name,

            "current_latitude": asset.current_latitude,

            "current_longitude": asset.current_longitude,

            "last_updated": asset.last_scanned_at,

            "path": path

        })

    return {

        "assets": response

    }


def get_tracking_session_details(
    db: Session,
    tracking_session_id: str,
    current_user
):
    """
    Get detailed information about a specific tracking session
    """

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

    user = (
        db.query(User)
        .filter(
            User.id == session.user_id
        )
        .first()
    )

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

    assets = []

    for mapping, asset in mappings:

        assets.append({

            "asset_id": asset.id,

            "asset_name": asset.name,

            "serial_number": asset.serial_number,

            "manufacturer": asset.manufacturer,

            "model": asset.model

        })

    return {

        "tracking_session_id": session.id,

        "status": session.status,

        "started_at": session.started_at,

        "ended_at": session.ended_at,

        "tracked_by_user_id": user.id,

        "tracked_by_name": user.full_name,

        "assets": assets
    }


def get_tracking_sessions(
    db: Session,
    current_user,
    page: int = 1,
    size: int = 20,
    status: str | None = None,
    user_id: str | None = None,
):
    """
    Get paginated list of tracking sessions with filters
    """

    query = (
        db.query(
            TrackingSession,
            User
        )
        .join(
            User,
            User.id == TrackingSession.user_id
        )
    )

    # -----------------------------------
    # Client Restriction
    # -----------------------------------

    if current_user["role"] != "ADMIN":

        query = query.filter(
            TrackingSession.client_id == current_user["client_id"]
        )

    # -----------------------------------
    # Filters
    # -----------------------------------

    if status:

        query = query.filter(
            TrackingSession.status == status
        )

    if user_id:

        query = query.filter(
            TrackingSession.user_id == user_id
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
            db.query(
                TrackingSessionAsset
            )
            .filter(
                TrackingSessionAsset.tracking_session_id == session.id
            )
            .count()
        )

        items.append({

            "tracking_session_id": session.id,

            "tracked_by_user_id": user.id,

            "tracked_by_name": user.full_name,

            "status": session.status,

            "started_at": session.started_at,

            "ended_at": session.ended_at,

            "tracked_assets": tracked_assets

        })

    return {

        "total": total,

        "page": page,

        "size": size,

        "items": items

    }


def get_tracking_history(
    db: Session,
    asset_id: str,
    current_user,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 1000
):
    """
    Get GPS history for a specific asset
    """

    asset = (
        db.query(Asset)
        .filter(
            Asset.id == asset_id
        )
        .first()
    )

    if not asset:

        raise HTTPException(
            status_code=404,
            detail="Asset not found."
        )

    # ----------------------------------
    # Client Restriction
    # ----------------------------------

    if current_user["role"] != "ADMIN":

        if asset.client_id != current_user["client_id"]:

            raise HTTPException(
                status_code=403,
                detail="Access denied."
            )

    query = (
        db.query(GPSLog)
        .filter(
            GPSLog.asset_id == asset.id
        )
    )

    if start_date:

        query = query.filter(
            GPSLog.recorded_at >= start_date
        )

    if end_date:

        query = query.filter(
            GPSLog.recorded_at <= end_date
        )

    logs = (
        query
        .order_by(
            GPSLog.recorded_at.asc()
        )
        .limit(limit)
        .all()
    )

    history = []

    for log in logs:

        history.append({

            "latitude": log.latitude,

            "longitude": log.longitude,

            "accuracy": log.accuracy,

            "speed": log.speed,

            "recorded_at": log.recorded_at,

            "tracking_session_id": log.tracking_session_id

        })

    return {

        "asset_id": asset.id,

        "asset_name": asset.name,

        "total_points": len(history),

        "history": history

    }