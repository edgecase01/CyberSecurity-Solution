"""Google OAuth2 client (authlib) for login + Gmail API scopes."""

from authlib.integrations.starlette_client import OAuth

from config import Settings, get_settings

GOOGLE_SCOPES = "openid email profile https://mail.google.com/"

oauth = OAuth()


def register_google_oauth(settings: Settings | None = None) -> OAuth:
    settings = settings or get_settings()
    if "google" in oauth._clients:
        return oauth
    oauth.register(
        name="google",
        client_id=settings.gmail_client_id,
        client_secret=settings.gmail_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": GOOGLE_SCOPES},
    )
    return oauth
