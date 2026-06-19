from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SubscriptionSummary(BaseModel):
    """Subscription details for dashboard"""
    licence_count: int
    used_licences: int
    max_assets: int
    max_departments: int
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None
    status: Optional[str] = None


class ClientDashboardResponse(BaseModel):
    """Complete client dashboard response"""
    total_departments: int
    total_users: int
    total_managers: int
    total_assets: int
    assigned_assets: int
    available_assets: int
    subscription: Optional[SubscriptionSummary] = None


class AdminDashboardResponse(BaseModel):
    """Admin dashboard with client-specific data"""
    client_id: str
    client_name: Optional[str] = None
    total_departments: int
    total_users: int
    total_managers: int
    total_assets: int
    assigned_assets: int
    available_assets: int
    subscription: Optional[SubscriptionSummary] = None


    
from pydantic import BaseModel


class PlatformDashboardResponse(BaseModel):
    total_clients: int
    active_clients: int
    inactive_clients: int

    total_subscriptions: int
    active_subscriptions: int
    expired_subscriptions: int

    total_users: int
    total_managers: int

    total_assets: int
    assigned_assets: int
    available_assets: int