from datetime import UTC, datetime, timedelta
from uuid import UUID

from jose import jwt

from config import Settings


def create_access_token(user_id: UUID, settings: Settings) -> tuple[str, int]:
    expires_minutes = settings.jwt_access_token_expire_minutes
    expire = datetime.now(UTC) + timedelta(minutes=expires_minutes)
    payload = {"sub": str(user_id), "exp": expire}
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, expires_minutes * 60
