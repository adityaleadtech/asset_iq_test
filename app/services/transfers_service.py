from sqlalchemy.orm import Session
from sqlalchemy import func, or_, String, text
from fastapi import HTTPException, status
from uuid import UUID
from datetime import datetime

from app.models.transfers_model import Transfer
from app.models.transfer_asset import TransferAsset
from app.models.asset import Asset
from app.models.departments import Department
from app.models.location import Location
from app.models.users import User

from app.schemas.transfers_schema import TransferCreate
from app.enums.transfer_types import TransferType


class TransferService:

    @staticmethod
    def create_transfer(
        transfer_data: TransferCreate,
        db: Session,
        current_user: dict
    ):
        """
        Create a new asset transfer.
        
        This is the only way to record asset movements. Transfers are immutable
        once created to maintain an accurate audit trail.
        """
        
        # ========== DEBUGGING START ==========
        print("=" * 80)
        print("🔍 DEBUG: CREATE TRANSFER")
        print(f"Transfer Type: {transfer_data.transfer_type}")
        print(f"Reason: {transfer_data.reason}")
        print(f"Remarks: {transfer_data.remarks}")
        print(f"Assets: {transfer_data.assets}")
        print(f"\nCurrent User: {current_user}")
        print(f"  - User ID: {current_user.get('id')}")
        print(f"  - Client ID: {current_user.get('client_id')}")
        print("=" * 80)
        # ========== DEBUGGING END ==========

        try:
            transfer = Transfer(
                client_id=current_user["client_id"],
                transfer_type=transfer_data.transfer_type,
                reason=transfer_data.reason,
                remarks=transfer_data.remarks,
                transferred_by=current_user["id"]
            )

            db.add(transfer)
            db.flush()

            processed_assets = set()

            for item in transfer_data.assets:
                
                print(f"\n📦 Processing Asset: {item.asset_id}")
                print(f"  - To Department ID: {item.to_department_id}")

                if str(item.asset_id) in processed_assets:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Duplicate asset {item.asset_id}."
                    )

                processed_assets.add(str(item.asset_id))

                # ============================================================
                # Find asset using text() for reliable UUID comparison
                # ============================================================
                asset = (
                    db.query(Asset)
                    .filter(
                        text("id = :asset_id AND client_id = :client_id")
                    )
                    .params(
                        asset_id=str(item.asset_id),
                        client_id=current_user["client_id"]
                    )
                    .first()
                )

                # Fallback to String cast if text() doesn't work
                if not asset:
                    asset = (
                        db.query(Asset)
                        .filter(
                            func.cast(Asset.id, String) == str(item.asset_id),
                            Asset.client_id == current_user["client_id"],
                        )
                        .first()
                    )

                if not asset:
                    # Check without client filter
                    asset_no_client = (
                        db.query(Asset)
                        .filter(func.cast(Asset.id, String) == str(item.asset_id))
                        .first()
                    )
                    
                    if asset_no_client:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Asset {item.asset_id} exists but belongs to a different client."
                        )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Asset {item.asset_id} not found in database."
                        )

                from_department = asset.department_id
                from_location = asset.location_id
                from_user = asset.assigned_to_user_id

                to_department = asset.department_id
                to_location = asset.location_id
                to_user = asset.assigned_to_user_id

                if transfer_data.transfer_type == TransferType.DEPARTMENT:

                    if not item.to_department_id:
                        raise HTTPException(
                            status_code=400,
                            detail="Destination department is required."
                        )

                    # Find department
                    department = (
                        db.query(Department)
                        .filter(
                            func.cast(Department.id, String) == str(item.to_department_id),
                            Department.client_id == current_user["client_id"],
                        )
                        .first()
                    )

                    if not department:
                        raise HTTPException(
                            status_code=404,
                            detail="Department not found."
                        )

                    # Check if it's a no-op transfer
                    if asset.department_id == department.id:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Asset {asset.name} is already assigned to this department."
                        )

                    asset.department_id = department.id
                    to_department = department.id

                elif transfer_data.transfer_type == TransferType.LOCATION:

                    if not item.to_location_id:
                        raise HTTPException(
                            status_code=400,
                            detail="Destination location is required."
                        )

                    # Find location
                    location = (
                        db.query(Location)
                        .filter(
                            func.cast(Location.id, String) == str(item.to_location_id),
                            Location.client_id == current_user["client_id"],
                        )
                        .first()
                    )

                    if not location:
                        raise HTTPException(
                            status_code=404,
                            detail="Location not found."
                        )

                    # Check if it's a no-op transfer
                    if asset.location_id == location.id:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Asset {asset.name} is already assigned to this location."
                        )

                    asset.location_id = location.id
                    to_location = location.id

                elif transfer_data.transfer_type == TransferType.USER:

                    if not item.to_user_id:
                        raise HTTPException(
                            status_code=400,
                            detail="Destination user is required."
                        )

                    # Find user
                    user = (
                        db.query(User)
                        .filter(
                            func.cast(User.id, String) == str(item.to_user_id),
                            User.client_id == current_user["client_id"],
                        )
                        .first()
                    )

                    if not user:
                        raise HTTPException(
                            status_code=404,
                            detail="User not found."
                        )

                    # Check if it's a no-op transfer
                    if asset.assigned_to_user_id == user.id:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Asset {asset.name} is already assigned to this user."
                        )

                    asset.assigned_to_user_id = user.id
                    to_user = user.id

                transfer_asset = TransferAsset(
                    transfer_id=transfer.id,
                    asset_id=asset.id,

                    from_department_id=from_department,
                    to_department_id=to_department,

                    from_location_id=from_location,
                    to_location_id=to_location,

                    from_user_id=from_user,
                    to_user_id=to_user
                )

                db.add(transfer_asset)

            db.commit()
            db.refresh(transfer)

            # ============================================================
            # Get the user who performed the transfer
            # ============================================================
            transferred_by_user = (
                db.query(User)
                .filter(User.id == transfer.transferred_by)
                .first()
            )

            # ============================================================
            # Count the number of assets in this transfer
            # ============================================================
            asset_count = (
                db.query(TransferAsset)
                .filter(TransferAsset.transfer_id == transfer.id)
                .count()
            )

            # ============================================================
            # Return properly formatted response matching TransferResponse schema
            # ============================================================
            response = {
                "id": str(transfer.id),
                "transfer_type": transfer.transfer_type,
                "reason": transfer.reason,
                "remarks": transfer.remarks,
                "transferred_by": transferred_by_user.full_name if transferred_by_user else None,
                "transferred_by_id": str(transfer.transferred_by) if transfer.transferred_by else None,
                "asset_count": asset_count,
                "created_at": transfer.created_at,
            }

            print("\n" + "=" * 80)
            print("✅ TRANSFER CREATED SUCCESSFULLY!")
            print(f"Transfer ID: {transfer.id}")
            print(f"Asset Count: {asset_count}")
            print("=" * 80)

            return response

        except HTTPException as e:
            print("\n" + "=" * 80)
            print(f"❌ HTTP EXCEPTION: {e.detail}")
            print(f"Status Code: {e.status_code}")
            print("=" * 80)
            db.rollback()
            raise

        except Exception as e:
            print("\n" + "=" * 80)
            print(f"❌ UNEXPECTED EXCEPTION: {str(e)}")
            import traceback
            traceback.print_exc()
            print("=" * 80)
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )

    @staticmethod
    def get_transfer(
        transfer_id: UUID,
        db: Session,
        current_user: dict
    ):
        """
        Get a specific transfer by ID with all asset details.
        """
        
        # Get the transfer
        transfer = (
            db.query(Transfer)
            .filter(
                Transfer.id == transfer_id,
                Transfer.client_id == current_user["client_id"]
            )
            .first()
        )

        if not transfer:
            raise HTTPException(
                status_code=404,
                detail="Transfer not found."
            )

        # Get the transfer assets
        transfer_assets = (
            db.query(TransferAsset)
            .filter(
                TransferAsset.transfer_id == transfer.id
            )
            .all()
        )

        # Build assets list with details
        assets = []
        
        for ta in transfer_assets:
            asset = (
                db.query(Asset)
                .filter(Asset.id == ta.asset_id)
                .first()
            )
            
            if not asset:
                continue
            
            # Get related entities
            from_department = (
                db.query(Department)
                .filter(Department.id == ta.from_department_id)
                .first()
            ) if ta.from_department_id else None
            
            to_department = (
                db.query(Department)
                .filter(Department.id == ta.to_department_id)
                .first()
            ) if ta.to_department_id else None
            
            from_location = (
                db.query(Location)
                .filter(Location.id == ta.from_location_id)
                .first()
            ) if ta.from_location_id else None
            
            to_location = (
                db.query(Location)
                .filter(Location.id == ta.to_location_id)
                .first()
            ) if ta.to_location_id else None
            
            from_user = (
                db.query(User)
                .filter(User.id == ta.from_user_id)
                .first()
            ) if ta.from_user_id else None
            
            to_user = (
                db.query(User)
                .filter(User.id == ta.to_user_id)
                .first()
            ) if ta.to_user_id else None

            assets.append({
                "asset_id": str(asset.id),
                "asset_name": asset.name,
                "asset_code": getattr(asset, "asset_code", None),
                "serial_number": getattr(asset, "serial_number", None),
                
                "from_department_id": str(ta.from_department_id) if ta.from_department_id else None,
                "from_department": from_department.name if from_department else None,
                "to_department_id": str(ta.to_department_id) if ta.to_department_id else None,
                "to_department": to_department.name if to_department else None,
                
                "from_location_id": str(ta.from_location_id) if ta.from_location_id else None,
                "from_location": from_location.name if from_location else None,
                "to_location_id": str(ta.to_location_id) if ta.to_location_id else None,
                "to_location": to_location.name if to_location else None,
                
                "from_user_id": str(ta.from_user_id) if ta.from_user_id else None,
                "from_user": from_user.full_name if from_user else None,
                "to_user_id": str(ta.to_user_id) if ta.to_user_id else None,
                "to_user": to_user.full_name if to_user else None,
            })

        # Get transferred by user details
        transferred_by = (
            db.query(User)
            .filter(User.id == transfer.transferred_by)
            .first()
        )

        return {
            "id": str(transfer.id),
            "transfer_type": transfer.transfer_type,
            "reason": transfer.reason,
            "remarks": transfer.remarks,
            "transferred_by": transferred_by.full_name if transferred_by else None,
            "transferred_by_id": str(transfer.transferred_by) if transfer.transferred_by else None,
            "created_at": transfer.created_at,
            "assets": assets
        }

    @staticmethod
    def get_transfers(
        db: Session,
        current_user: dict,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
        transfer_type: TransferType | None = None,
        transferred_by: UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ):
        """
        Get paginated list of transfers with filters.
        """
        
        query = (
            db.query(Transfer)
            .filter(
                Transfer.client_id == current_user["client_id"]
            )
        )
        
        # Apply filters
        if transfer_type:
            query = query.filter(Transfer.transfer_type == transfer_type)
        
        if transferred_by:
            query = query.filter(Transfer.transferred_by == transferred_by)
        
        if start_date:
            query = query.filter(Transfer.created_at >= start_date)
        
        if end_date:
            query = query.filter(Transfer.created_at <= end_date)
        
        if search:
            # Search in transfer reason or remarks using COALESCE to handle NULL
            query = query.filter(
                func.coalesce(Transfer.reason, "").ilike(f"%{search}%") |
                func.coalesce(Transfer.remarks, "").ilike(f"%{search}%")
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        transfers = (
            query.order_by(Transfer.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        
        # Build response items
        items = []
        
        for transfer in transfers:
            # Get transferred by user
            transferred_by_user = (
                db.query(User)
                .filter(User.id == transfer.transferred_by)
                .first()
            )
            
            # Get count of assets in this transfer
            asset_count = (
                db.query(TransferAsset)
                .filter(TransferAsset.transfer_id == transfer.id)
                .count()
            )
            
            items.append({
                "id": str(transfer.id),
                "transfer_type": transfer.transfer_type,
                "reason": transfer.reason,
                "remarks": transfer.remarks,
                "transferred_by": transferred_by_user.full_name if transferred_by_user else None,
                "transferred_by_id": str(transfer.transferred_by) if transfer.transferred_by else None,
                "asset_count": asset_count,
                "created_at": transfer.created_at,
            })
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }

    @staticmethod
    def get_transfer_dashboard(
        db: Session,
        current_user: dict,
        start_date: datetime | None = None,
        end_date: datetime | None = None
    ):
        """
        Get dashboard statistics for transfers.
        
        Returns explicit fields for easier frontend consumption:
        - total_transfers
        - department_transfers
        - location_transfers
        - user_transfers
        - total_assets_transferred
        - recent_transfers
        """
        
        query = (
            db.query(Transfer)
            .filter(
                Transfer.client_id == current_user["client_id"]
            )
        )
        
        if start_date:
            query = query.filter(Transfer.created_at >= start_date)
        
        if end_date:
            query = query.filter(Transfer.created_at <= end_date)
        
        total_transfers = query.count()
        
        # Count by transfer type (explicit fields)
        department_transfers = query.filter(
            Transfer.transfer_type == TransferType.DEPARTMENT
        ).count()
        
        location_transfers = query.filter(
            Transfer.transfer_type == TransferType.LOCATION
        ).count()
        
        user_transfers = query.filter(
            Transfer.transfer_type == TransferType.USER
        ).count()
        
        # Get total assets transferred
        total_assets = (
            db.query(TransferAsset)
            .join(Transfer)
            .filter(
                Transfer.client_id == current_user["client_id"]
            )
            .count()
        )
        
        # Get recent transfers (last 5)
        recent_transfers = (
            query.order_by(Transfer.created_at.desc())
            .limit(5)
            .all()
        )
        
        recent_items = []
        for transfer in recent_transfers:
            transferred_by_user = (
                db.query(User)
                .filter(User.id == transfer.transferred_by)
                .first()
            )
            
            asset_count = (
                db.query(TransferAsset)
                .filter(TransferAsset.transfer_id == transfer.id)
                .count()
            )
            
            recent_items.append({
                "id": str(transfer.id),
                "transfer_type": transfer.transfer_type,
                "reason": transfer.reason,
                "transferred_by": transferred_by_user.full_name if transferred_by_user else None,
                "asset_count": asset_count,
                "created_at": transfer.created_at,
            })
        
        return {
            "total_transfers": total_transfers,
            "department_transfers": department_transfers,
            "location_transfers": location_transfers,
            "user_transfers": user_transfers,
            "total_assets_transferred": total_assets,
            "recent_transfers": recent_items,
            "start_date": start_date,
            "end_date": end_date
        }

    @staticmethod
    def get_my_transfers(
        db: Session,
        current_user: dict
    ):
        """
        Get transfers where the current user is involved.
        
        A user is considered involved if:
        - They initiated the transfer (transferred_by), OR
        - Assets were transferred FROM them (from_user_id), OR
        - Assets were transferred TO them (to_user_id)
        
        Uses a single optimized query with or_() for better readability.
        """
        
        # Single query with or_() conditions
        transfers = (
            db.query(Transfer)
            .join(TransferAsset)
            .filter(
                Transfer.client_id == current_user["client_id"],
                or_(
                    Transfer.transferred_by == current_user["id"],
                    TransferAsset.from_user_id == current_user["id"],
                    TransferAsset.to_user_id == current_user["id"],
                )
            )
            .distinct()
            .order_by(Transfer.created_at.desc())
            .all()
        )
        
        # Build response
        items = []
        for transfer in transfers:
            transferred_by_user = (
                db.query(User)
                .filter(User.id == transfer.transferred_by)
                .first()
            )
            
            asset_count = (
                db.query(TransferAsset)
                .filter(TransferAsset.transfer_id == transfer.id)
                .count()
            )
            
            items.append({
                "id": str(transfer.id),
                "transfer_type": transfer.transfer_type,
                "reason": transfer.reason,
                "remarks": transfer.remarks,
                "transferred_by": transferred_by_user.full_name if transferred_by_user else None,
                "transferred_by_id": str(transfer.transferred_by) if transfer.transferred_by else None,
                "asset_count": asset_count,
                "created_at": transfer.created_at,
            })
        
        return items

    @staticmethod
    def get_transfer_report(
        transfer_id: UUID,
        db: Session,
        current_user: dict
    ):
        """
        Get a detailed report for a specific transfer.
        
        Currently returns the same data as get_transfer().
        Future enhancement: Generate PDF report.
        """
        
        # Reuse get_transfer to get all details
        transfer = TransferService.get_transfer(
            transfer_id=transfer_id,
            db=db,
            current_user=current_user
        )
        
        # Add report metadata
        transfer["report_generated_at"] = datetime.utcnow()
        transfer["report_generated_by"] = current_user.get("full_name", "Unknown")
        
        return transfer