from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.config.dependencies import (
    get_db,
    get_current_user,
)

from app.schemas.dashboard import (
    ClientDashboardResponse,
    PlatformDashboardResponse,
)

from app.services.dashboard import (
    get_dashboard,
    _get_client_dashboard,
    _get_platform_dashboard,
)

from app.utils.auth import admin_required


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


# ============================================================
# UNIFIED DASHBOARD
# ============================================================


@router.get(
    "",
    summary="Get Role-Based Unified Dashboard",
    description="""
Returns the dashboard automatically based on the authenticated user's role.

This is the **recommended dashboard endpoint for both the web application
and mobile application**.

The backend reads the authenticated user's JWT token and determines the
dashboard level automatically.

---

## Supported Roles

### ADMIN / Platform Admin

Without query parameters:

`GET /dashboard`

Returns the complete platform dashboard.

The platform dashboard contains:

- Total clients
- Active clients
- Inactive clients
- Total subscriptions
- Active subscriptions
- Expired subscriptions
- Total users
- Total client admins
- Total managers
- Total normal users
- Total departments
- Total assets
- Assigned assets
- Unassigned assets
- Tagged assets
- Untagged assets
- Active assets
- Inactive assets
- Damaged assets
- Assets under maintenance
- Lost assets
- Recent clients
- Recent subscriptions

### Platform Admin Client Dashboard

Send:

`GET /dashboard?client_id={client_id}`

The API returns the dashboard of the specified client.

Example:

`GET /dashboard?client_id=550e8400-e29b-41d4-a716-446655440000`

### Platform Admin Department Dashboard

Send:

`GET /dashboard?department_id={department_id}`

Optionally include the client ID:

`GET /dashboard?client_id={client_id}&department_id={department_id}`

The API returns the dashboard of the specified department.

### Platform Admin User Dashboard

Send:

`GET /dashboard?user_id={user_id}`

Optional filters:

`GET /dashboard?client_id={client_id}&department_id={department_id}&user_id={user_id}`

The API returns the personal dashboard of the selected user.

---

## CLIENT_ADMIN

Without query parameters:

`GET /dashboard`

Returns the dashboard for the Client Admin's own client.

The `client_id` is automatically read from the JWT token.

A Client Admin **cannot access another client's dashboard**.

### Client Admin Department Dashboard

Send:

`GET /dashboard?department_id={department_id}`

The department must belong to the Client Admin's client.

### Client Admin User Dashboard

Send:

`GET /dashboard?user_id={user_id}`

The user must belong to the Client Admin's client.

---

## MANAGER

Send:

`GET /dashboard`

The Manager automatically receives the dashboard of their assigned department.

The following information is returned:

- Department information
- Assigned manager
- Total team members
- Total managers
- Total users
- Total department assets
- Assigned assets
- Unassigned assets
- Tagged assets
- Untagged assets
- Active assets
- Inactive assets
- Damaged assets
- Assets under maintenance
- Lost assets
- Team member list
- Recent assets

The department is automatically identified from the JWT token.

Managers cannot access another department's dashboard.

Managers cannot access individual user dashboards.

---

## USER

Send:

`GET /dashboard`

The user automatically receives their personal dashboard.

The dashboard contains:

- User profile
- Department information
- Department manager
- Total assigned assets
- Tagged assets
- Untagged assets
- Active assets
- Inactive assets
- Damaged assets
- Assets under maintenance
- Lost assets
- Complete assigned asset list

The user ID is automatically read from the JWT token.

Users cannot access another user's dashboard.

---

## Dashboard Selection Priority

When multiple query parameters are supplied, the dashboard is selected in
the following order:

1. `user_id`
2. `department_id`
3. `client_id`
4. Default dashboard based on authenticated role

For example:

`GET /dashboard?client_id=CLIENT_ID&department_id=DEPARTMENT_ID&user_id=USER_ID`

returns the **User Dashboard**.

---

## Authentication

A valid Bearer JWT token is required.

Example Authorization header:

`Authorization: Bearer YOUR_JWT_TOKEN`

The role, client ID, department ID, and user ID are read from the token.

---

## Recommended Usage

Frontend applications should normally use only this endpoint:

`GET /dashboard`

The backend automatically determines the correct dashboard based on the
authenticated user's role.

Query parameters should only be used when an Admin or Client Admin is
drilling down into a client, department, or user dashboard.
""",
    responses={
        200: {
            "description": "Dashboard returned successfully.",
        },
        400: {
            "description": (
                "The authenticated user is missing required client "
                "or department information."
            ),
        },
        401: {
            "description": (
                "Authentication token is missing, invalid, or expired."
            ),
        },
        403: {
            "description": (
                "The authenticated user does not have permission to "
                "access the requested dashboard."
            ),
        },
        404: {
            "description": (
                "The requested client, department, or user was not found."
            ),
        },
    },
)
def get_unified_dashboard(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    client_id: Optional[str] = Query(
        default=None,
        description=(
            "Client ID used to drill down into a client dashboard. "
            "Mainly intended for Platform Admin."
        ),
    ),
    department_id: Optional[str] = Query(
        default=None,
        description=(
            "Department ID used to drill down into a department dashboard. "
            "Available to Platform Admin and Client Admin based on access."
        ),
    ),
    user_id: Optional[str] = Query(
        default=None,
        description=(
            "User ID used to view an individual user's dashboard. "
            "Available to Platform Admin and Client Admin based on access."
        ),
    ),
):
    """
    Return the dashboard appropriate for the authenticated user's role.
    """

    return get_dashboard(
        db=db,
        current_user=current_user,
        client_id=client_id,
        department_id=department_id,
        user_id=user_id,
    )


# ============================================================
# PLATFORM DASHBOARD
# ============================================================


@router.get(
    "/platform",
    response_model=PlatformDashboardResponse,
    summary="Get Complete Platform Dashboard",
    description="""
Returns the complete AssetIQ platform-level dashboard.

This endpoint is available **only to Platform Admins (`ADMIN`)**.

---

## How to Use

Send:

`GET /dashboard/platform`

No query parameters are required.

A valid Platform Admin JWT token must be provided.

Example:

`Authorization: Bearer PLATFORM_ADMIN_JWT_TOKEN`

---

## Dashboard Information

The response contains platform-wide statistics.

### Client Statistics

- Total clients
- Active clients
- Inactive clients

### Subscription Statistics

- Total subscriptions
- Active subscriptions
- Expired subscriptions

### User Statistics

- Total active users
- Client Admin count
- Manager count
- Normal user count

### Department Statistics

- Total active departments

### Asset Statistics

- Total assets
- Assigned assets
- Unassigned assets
- Tagged assets
- Untagged assets
- Active assets
- Inactive assets
- Damaged assets
- Assets under maintenance
- Lost assets

### Recent Clients

Returns the latest 5 clients created on the platform.

### Recent Subscriptions

Returns the latest 5 subscriptions created on the platform.

---

## Recommended Usage

Use this endpoint for the Platform Admin dashboard home page.

For normal application usage, `GET /dashboard` is preferred because the
dashboard level is selected automatically from the authenticated user's role.
""",
    responses={
        200: {
            "description": "Platform dashboard returned successfully.",
        },
        401: {
            "description": "Invalid or expired authentication token.",
        },
        403: {
            "description": "Platform Admin access is required.",
        },
    },
)
def fetch_platform_dashboard(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(admin_required),
):
    """
    Return complete platform statistics for a Platform Admin.
    """

    return _get_platform_dashboard(
        db=db,
    )


# ============================================================
# CLIENT DASHBOARD
# ============================================================


@router.get(
    "/client",
    response_model=ClientDashboardResponse,
    summary="Get Client Dashboard",
    description="""
Returns the complete dashboard for a specific AssetIQ client.

This endpoint supports:

- `ADMIN`
- `CLIENT_ADMIN`

---

## CLIENT_ADMIN Usage

A Client Admin should send:

`GET /dashboard/client`

No `client_id` query parameter is required.

The client ID is automatically read from the authenticated user's JWT token.

Example:

`Authorization: Bearer CLIENT_ADMIN_JWT_TOKEN`

The Client Admin can only access their own client's dashboard.

---

## ADMIN Usage

A Platform Admin must provide the client ID.

Send:

`GET /dashboard/client?client_id={client_id}`

Example:

`GET /dashboard/client?client_id=550e8400-e29b-41d4-a716-446655440000`

---

## Dashboard Information

### Client Information

- Client ID
- Client name
- Client code
- Client status
- Client creation date

### Subscription Information

- Subscription ID
- Subscription status
- Licence count
- Used licences
- Available licences
- Licence usage percentage
- Maximum assets
- Maximum departments
- Subscription price
- Subscription start date
- Subscription end date
- Auto-renew status

### User Statistics

- Total users
- Client Admin count
- Manager count
- Normal user count

### Department Statistics

- Total departments

### Asset Statistics

- Total assets
- Assigned assets
- Unassigned assets
- Tagged assets
- Untagged assets
- Active assets
- Inactive assets
- Damaged assets
- Assets under maintenance
- Lost assets

### Department Breakdown

Each department contains:

- Department ID
- Department name
- Department code
- Assigned manager
- Total department users
- Total department assets
- Department status

### Recent Users

Returns the latest 5 active users created for the client.

### Recent Assets

Returns the latest 10 active assets created for the client.

---

## Recommended Usage

Use this endpoint when a Platform Admin explicitly opens a client's dashboard.

Client Admin applications can either use this endpoint or the unified:

`GET /dashboard`

The unified endpoint is recommended because it automatically reads the
Client Admin's client ID from the JWT token.
""",
    responses={
        200: {
            "description": "Client dashboard returned successfully.",
        },
        400: {
            "description": (
                "Client ID is required when the authenticated user is ADMIN."
            ),
        },
        401: {
            "description": "Invalid or expired authentication token.",
        },
        403: {
            "description": (
                "The authenticated user cannot access the requested client."
            ),
        },
        404: {
            "description": "Client was not found.",
        },
    },
)
def get_client_dashboard_endpoint(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    client_id: Optional[str] = Query(
        default=None,
        description=(
            "Client ID. Required for ADMIN. "
            "CLIENT_ADMIN automatically uses the client ID from the JWT."
        ),
    ),
):
    """
    Return the dashboard for a specific client.
    """

    role = str(
        current_user.get("role", "")
    ).upper()

    if role in {"ADMIN", "PLATFORM_ADMIN"}:

        if not client_id:
            raise HTTPException(
                status_code=400,
                detail="client_id is required for Platform Admin.",
            )

        target_client_id = client_id

    elif role == "CLIENT_ADMIN":

        target_client_id = current_user.get(
            "client_id"
        )

        if not target_client_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Client Admin is not associated "
                    "with any client."
                ),
            )

        if (
            client_id
            and client_id != target_client_id
        ):
            raise HTTPException(
                status_code=403,
                detail=(
                    "Client Admin cannot access "
                    "another client's dashboard."
                ),
            )

    else:

        raise HTTPException(
            status_code=403,
            detail=(
                "Only Platform Admin or Client Admin "
                "can access the client dashboard."
            ),
        )

    return _get_client_dashboard(
        db=db,
        client_id=target_client_id,
    )