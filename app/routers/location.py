from fastapi import (
    APIRouter,
    Depends,
    Query,
    status
)
from sqlalchemy.orm import Session

from app.config.dependencies import get_db
from app.enums.location_type import LocationType
from app.schemas.location import (
    LocationCardResponse,
    LocationCreate,
    LocationDropdownResponse,
    LocationLeafPathResponse,
    LocationMigrationRequest,
    LocationPathCreate,
    LocationPathResponse,
    LocationResponse
)
from app.routers.asset import (
    check_permission
)
from app.services.location import close_location, create_location, create_location_path, get_location_cards, get_location_dropdown, get_location_leaf_path, migrate_location



router= APIRouter(prefix="/location",
    tags=["locations"])

@router.post(
    "/path",
    response_model=LocationPathResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Location Hierarchy",
    description="""
Create an entire location hierarchy in a single request.

The backend automatically:

1. Converts names to uppercase.
2. Finds existing locations.
3. Creates only missing locations.
4. Automatically assigns parent locations.
5. Returns the final leaf location.

Example:

INDIA
└── MAHARASHTRA
    └── PUNE
        └── OFFICE 12

Request:

{
  "path": [
    {
      "name": "India",
      "location_type": "COUNTRY"
    },
    {
      "name": "Maharashtra",
      "location_type": "STATE"
    },
    {
      "name": "Pune",
      "location_type": "CITY"
    },
    {
      "name": "Office 12",
      "location_type": "OFFICE"
    }
  ]
}

If INDIA and MAHARASHTRA already exist,
only PUNE and OFFICE 12 will be created.
"""
)
def create_location_hierarchy(
    payload: LocationPathCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "LOCATION_MANAGEMENT",
            "create"
        )
    ),
    c_id: str | None=None
):
    return create_location_path(
        db,
        payload,
        current_user,
        c_id
    )



@router.get(
    "/dropdown",
    response_model=list[
        LocationDropdownResponse
    ],
    summary="Fetch Location Dropdown",
    description="""
Fetch locations for dropdowns.

Examples:

Get root locations:

GET /locations/dropdown

Get children:

GET /locations/dropdown?
parent_location_id=<id>

Get only offices:

GET /locations/dropdown?
location_type=OFFICE

Search:

GET /locations/dropdown?
search=pun

This endpoint is intended for:

- Cascading location selectors
- Asset creation
- Department creation
- Asset transfers
- Geofencing
- Mobile application dropdowns
"""
)
def get_location_dropdown_router(
    parent_location_id: str | None = Query(
        None,
        description=(
            "Parent location id. "
            "Returns direct children."
        )
    ),
    location_type: LocationType | None = Query(
        None,
        description=(
            "Filter by location type."
        )
    ),
    search: str | None = Query(
        None,
        description=(
            "Search by location name."
        )
    ),
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "LOCATION_MANAGEMENT",
            "read"
        )
    ),
    client_id: str | None = None
):
    return (
get_location_dropdown(
            db,
            current_user,
            parent_location_id,
            location_type,
            search,
            client_id
        )
    )



@router.get(
    "/{location_id}/leaf-path",
    response_model=LocationLeafPathResponse,
    summary="Get Full Location Path",
    description="""
Returns the complete hierarchy path
for a location.

Example:

INDIA
└── MAHARASHTRA
    └── PUNE
        └── OFFICE 12

returns:

INDIA > MAHARASHTRA > PUNE > OFFICE 12
"""
)
def get_location_leaf_path_router(
    location_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "LOCATION_MANAGEMENT",
            "read"
        )
    ),
    client_id:str|None =None
):
    return (
        get_location_leaf_path(
            db,
            location_id,
            current_user,
            client_id
        )
    )




# routers/location.py

@router.post(
    "/migrate",
    status_code=200,
    summary="Migrate Location",
    description="""
Create a new location hierarchy and
move all assets and departments
from the current location to the
new leaf location.

Example:

BENGALURU OFFICE
        ↓
JAIPUR OFFICE 12

The destination hierarchy is
automatically created if it does
not already exist.
"""
    
)
def migrate_location_router(
    payload: LocationMigrationRequest,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "LOCATION_MANAGEMENT",
            "update"
        )
    )
):
    return (
    migrate_location(
            db=db,
            payload=payload,
            current_user=current_user,
        )
    )




@router.post(
    "/{location_id}/close",
    summary="Close Location",
    description="""
Permanently close a location.

Actions:

1. Deactivate location
2. Deactivate child locations
3. Deactivate assets
4. Deactivate departments

This operation does not delete records.
History and audit logs remain intact.
"""
)
def close_location_router(
    location_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        check_permission(
            "LOCATION_MANAGEMENT",
            "delete"
        )
    )
):
    return close_location(
        db,
        location_id,
        current_user
    )


@router.get(
    "/cards",
    response_model=list[
        LocationCardResponse
    ],
    summary="Get Leaf Location Cards",
    description="""
Returns only leaf locations.

Each location contains its complete
hierarchy path from the root node.

Example:

OFFICE A
INDIA > KARNATAKA >
BENGALURU > OFFICE A

OFFICE 12
INDIA > RAJASTHAN >
JAIPUR > OFFICE 12
"""
)
def get_location_cards_router(
    db: Session = Depends(
        get_db
    ),
    current_user=Depends(
        check_permission(
            "LOCATION_MANAGEMENT",
            "read"
        )
    ),
    client_id: str | None = None
):
    return (
    get_location_cards(
            db,
            current_user,
            client_id
        )
    )



