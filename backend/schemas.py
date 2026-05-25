from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, HttpUrl

from models import ScanJobStatus, ScanType, ThreatStatus


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    name: str | None
    picture_url: str | None

    model_config = {"from_attributes": True}


class WebsiteScanRequest(BaseModel):
    url: HttpUrl


class WebsiteScanResponse(BaseModel):
    url: str
    status: ScanJobStatus
    threat_status: ThreatStatus | None = None
    cache_hit: bool
    scan_id: UUID | None = None
    result: dict | None = None
    scanned_at: datetime | None = None
    message: str | None = None


class ScanHistoryResponse(BaseModel):
    id: UUID
    user_id: UUID
    type: ScanType
    status: ThreatStatus
    scanned_at: datetime
    url: str | None

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    total_scanned: int
    threats_blocked: int
    recent_scans: list[ScanHistoryResponse]
