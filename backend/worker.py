"""
Celery worker for heavy background tasks (email scanning).

Run locally:
  celery -A worker.celery_app worker --loglevel=info
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from celery import Celery
from sqlalchemy import select

from config import get_settings
from database_sync import SyncSessionLocal
from ml_service import ScamModelPredictor
from models import ScanHistory, ScanType, ThreatStatus, User
from services.gmail_api import (
    build_gmail_credentials,
    build_gmail_service,
    get_message_content,
    list_unread_message_ids,
    quarantine_message,
)

settings = get_settings()
_predictor = ScamModelPredictor()

celery_app = Celery(
    "cybersec_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,
    worker_prefetch_multiplier=1,
)


def _persist_refreshed_access_token(db, user: User, credentials) -> None:
    if credentials.token and credentials.token != user.google_access_token:
        user.google_access_token = credentials.token
        db.add(user)
        db.commit()


def _process_email_message(
    db,
    user: User,
    service,
    message_id: str,
) -> dict:
    content = get_message_content(service, message_id)
    ml_prediction = _predictor.predict_text(content.body, content.subject)
    is_scam = bool(ml_prediction.get("is_scam"))

    threat_status = ThreatStatus.SCAM if is_scam else ThreatStatus.SAFE
    scanned_at = datetime.now(UTC)

    quarantine_result = None
    quarantined = False
    if is_scam:
        quarantine_result = quarantine_message(service, content.id, use_spam_label=True)
        quarantined = True

    scan_payload = {
        "gmail_message_id": content.id,
        "thread_id": content.thread_id,
        "subject": content.subject,
        "sender": content.sender,
        "body_preview": content.body[:500],
        "ml_prediction": ml_prediction,
        "quarantined": quarantined,
        "quarantine_result": quarantine_result,
    }

    scan_record = ScanHistory(
        user_id=user.id,
        type=ScanType.EMAIL,
        status=threat_status,
        scanned_at=scanned_at,
        url=f"gmail:message:{content.id}",
        result=json.dumps(scan_payload),
    )
    db.add(scan_record)
    db.commit()
    db.refresh(scan_record)

    return {
        "scan_id": str(scan_record.id),
        "message_id": content.id,
        "subject": content.subject,
        "status": threat_status.value,
        "ml_prediction": ml_prediction,
        "quarantined": quarantined,
    }


@celery_app.task(name="scan_email_task", bind=True)
def scan_email_task(self, user_id: str) -> dict:
    """
    Background task:
      1. Load user's google_refresh_token from PostgreSQL
      2. Fetch up to 5 unread Gmail messages
      3. Run ML on subject + body
      4. Persist ScanHistory per message
      5. If scam: remove INBOX and add SPAM label via Gmail API
    """
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError as exc:
        return {
            "task_id": self.request.id,
            "error": f"Invalid user_id: {user_id}",
            "processed": 0,
            "messages": [],
        }

    with SyncSessionLocal() as db:
        user = db.execute(select(User).where(User.id == user_uuid)).scalar_one_or_none()
        if user is None:
            return {
                "task_id": self.request.id,
                "error": "User not found",
                "processed": 0,
                "messages": [],
            }

        if not user.google_refresh_token:
            return {
                "task_id": self.request.id,
                "error": "User has no Google refresh token. Sign in again via /auth/login.",
                "processed": 0,
                "messages": [],
            }

        credentials = build_gmail_credentials(user, settings)
        _persist_refreshed_access_token(db, user, credentials)

        service = build_gmail_service(user, settings, credentials=credentials)
        unread = list_unread_message_ids(service, max_results=5)

        results = []
        for item in unread:
            message_id = item["id"]
            try:
                results.append(_process_email_message(db, user, service, message_id))
            except Exception as exc:
                db.rollback()
                results.append(
                    {
                        "message_id": message_id,
                        "error": str(exc),
                        "status": "error",
                    }
                )

        quarantined_count = sum(1 for item in results if item.get("quarantined"))
        return {
            "task_id": self.request.id,
            "user_id": user_id,
            "processed": len(results),
            "quarantined": quarantined_count,
            "messages": results,
        }
