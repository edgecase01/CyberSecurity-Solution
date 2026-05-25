from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from dependencies_auth import get_current_user
from models import User
from worker import scan_email_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


class EmailScanTaskResponse(BaseModel):
    task_id: str
    status: str


@router.post("/scan-email", response_model=EmailScanTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_email_scan(
    current_user: Annotated[User, Depends(get_current_user)],
) -> EmailScanTaskResponse:
    """Queue background Gmail scan for the authenticated user (uses stored refresh token)."""
    async_result = scan_email_task.delay(str(current_user.id))
    return EmailScanTaskResponse(task_id=async_result.id, status="queued")
