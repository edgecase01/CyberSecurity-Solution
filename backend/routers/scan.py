import json
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings, get_settings
from database import get_db
from dependencies import get_redis
from dependencies_auth import get_current_user, get_optional_user
from models import ScanHistory, ScanJobStatus, ScanType, ThreatStatus, User
from schemas import ScanHistoryResponse, WebsiteScanRequest, WebsiteScanResponse
from services.scan_cache import get_cached_scan, normalize_url, set_scan_completed
from services.website_scan import result_to_json, run_website_scan

router = APIRouter(prefix="/scan", tags=["scan"])


def _threat_status_from_result(scan_result: dict) -> ThreatStatus:
    is_scam = bool(scan_result.get("prediction", {}).get("is_scam"))
    return ThreatStatus.SCAM if is_scam else ThreatStatus.SAFE


@router.post("/website", response_model=WebsiteScanResponse)
async def scan_website(
    body: WebsiteScanRequest,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
    current_user: Annotated[User | None, Depends(get_optional_user)] = None,
) -> WebsiteScanResponse:
    """
    Check Redis for a recent scan (24h TTL).
    On cache miss: scrape the URL, run ML prediction, cache and return the result.
    Authenticated users get a ScanHistory row linked to their tenant (user_id).
    """
    url = str(body.url)
    normalized = normalize_url(url)
    cached = await get_cached_scan(redis, normalized)

    if cached and cached.get("status") == ScanJobStatus.COMPLETED.value:
        scanned_at = cached.get("scanned_at")
        threat = None
        if cached.get("result"):
            threat = _threat_status_from_result(cached["result"])
        return WebsiteScanResponse(
            url=normalized,
            status=ScanJobStatus.COMPLETED,
            threat_status=threat,
            cache_hit=True,
            result=cached.get("result"),
            scanned_at=datetime.fromisoformat(scanned_at) if scanned_at else None,
            message="Scan result served from cache.",
        )

    try:
        scan_result = await run_website_scan(
            normalized,
            timeout=settings.scan_request_timeout_seconds,
        )
    except Exception as exc:
        if current_user is not None:
            scan_record = ScanHistory(
                user_id=current_user.id,
                type=ScanType.WEBSITE,
                status=ThreatStatus.SAFE,
                url=normalized,
                scanned_at=datetime.now(UTC),
                result=json.dumps({"error": str(exc)}),
            )
            db.add(scan_record)
            await db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to scan URL: {exc}",
        ) from exc

    scanned_at_str = await set_scan_completed(redis, normalized, scan_result, settings)
    scanned_at = datetime.fromisoformat(scanned_at_str)
    threat_status = _threat_status_from_result(scan_result)

    scan_id = None
    if current_user is not None:
        scan_record = ScanHistory(
            user_id=current_user.id,
            type=ScanType.WEBSITE,
            status=threat_status,
            url=normalized,
            scanned_at=scanned_at,
            result=result_to_json(scan_result),
        )
        db.add(scan_record)
        await db.commit()
        await db.refresh(scan_record)
        scan_id = scan_record.id

    return WebsiteScanResponse(
        url=normalized,
        status=ScanJobStatus.COMPLETED,
        threat_status=threat_status,
        cache_hit=False,
        scan_id=scan_id,
        result=scan_result,
        scanned_at=scanned_at,
        message="Scan completed.",
    )


@router.get("/history", response_model=list[ScanHistoryResponse])
async def list_scan_history(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> list[ScanHistoryResponse]:
    """List scan history for the authenticated tenant."""
    from sqlalchemy import select

    result = await db.execute(
        select(ScanHistory)
        .where(ScanHistory.user_id == current_user.id)
        .order_by(ScanHistory.scanned_at.desc())
        .limit(100)
    )
    rows = result.scalars().all()
    return [ScanHistoryResponse.model_validate(row) for row in rows]
