from pydantic import BaseModel
from typing import Optional


class AssetTransferRequest(BaseModel):
    location_id: Optional[str] = None
    department_id: Optional[str] = None
    assigned_to_user_id: Optional[str] = None
    transfer_reason: Optional[str] = None
    notes: Optional[str] = None

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TransferResponse(BaseModel):
    id: str
    asset_id: str
    client_id: str

    from_location_id: Optional[str]
    to_location_id: Optional[str]

    from_department_id: Optional[str]
    to_department_id: Optional[str]

    from_user_id: Optional[str]
    to_user_id: Optional[str]

    transfer_type: str
    transfer_reason: Optional[str]
    notes: Optional[str]

    status: str
    transferred_by: str
    transferred_at: datetime

    class Config:
        from_attributes = True



from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TransferHistoryResponse(BaseModel):
    id: str

    transfer_type: str
    transfer_reason: Optional[str]

    from_location: Optional[str]
    to_location: Optional[str]

    from_department: Optional[str]
    to_department: Optional[str]

    from_user: Optional[str]
    to_user: Optional[str]

    notes: Optional[str]

    status: str

    transferred_by: Optional[str]
    transferred_at: datetime

    class Config:
        from_attributes = True