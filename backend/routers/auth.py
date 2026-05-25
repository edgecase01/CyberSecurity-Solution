from urllib.parse import urlencode

from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import Settings, get_settings
from database import get_db
from models import User
from services.google_oauth import oauth
from services.jwt_tokens import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


def _ensure_oauth_configured(settings: Settings) -> None:
    if not settings.gmail_client_id or not settings.gmail_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured (GMAIL_CLIENT_ID / GMAIL_CLIENT_SECRET).",
        )


@router.get("/login")
async def auth_login(request: Request, settings: Settings = Depends(get_settings)):
    """
    Redirect to Google's consent screen.
    Requests offline access (refresh token) and Gmail API scope.
    """
    _ensure_oauth_configured(settings)

    return await oauth.google.authorize_redirect(
        request,
        settings.google_redirect_uri,
        access_type="offline",
        prompt="consent",
    )


@router.get("/callback")
async def auth_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    Handle Google's redirect: persist tokens, issue app JWT, redirect to frontend.
    """
    _ensure_oauth_configured(settings)

    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth failed: {exc.error}",
        ) from exc

    userinfo = token.get("userinfo")
    if not userinfo:
        userinfo_response = await oauth.google.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            token=token,
        )
        userinfo = userinfo_response.json()

    google_sub = userinfo.get("sub")
    email = userinfo.get("email")
    if not google_sub or not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google did not return required user profile (sub, email).",
        )

    access_token = token.get("access_token")
    refresh_token = token.get("refresh_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google did not return an access token.",
        )

    result = await db.execute(select(User).where(User.google_sub == google_sub))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            google_sub=google_sub,
            email=email,
            name=userinfo.get("name"),
            picture_url=userinfo.get("picture"),
            google_access_token=access_token,
            google_refresh_token=refresh_token,
        )
        db.add(user)
    else:
        user.email = email
        user.name = userinfo.get("name")
        user.picture_url = userinfo.get("picture")
        user.google_access_token = access_token
        if refresh_token:
            user.google_refresh_token = refresh_token

    await db.commit()
    await db.refresh(user)

    app_jwt, _expires_in = create_access_token(user.id, settings)

    query = urlencode({"token": app_jwt})
    redirect_url = f"{settings.frontend_url.rstrip('/')}/auth/callback?{query}"
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
