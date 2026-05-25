from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from config import get_settings
from database import AsyncSession, engine, get_db
from dependencies import close_redis, init_redis
from dependencies_auth import get_current_user
from models import ScanHistory, ThreatStatus, User
from schemas import DashboardStats, ScanHistoryResponse
from routers import auth, chat, scan, tasks
from sqlalchemy import desc, func, select
from services.google_oauth import register_google_oauth

settings = get_settings()
register_google_oauth(settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = init_redis(settings.redis_url)

    yield

    await close_redis()
    await engine.dispose()


app = FastAPI(
    title="Cybersec Core API",
    description="Core backend for authentication and website scanning.",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.jwt_secret_key,
    same_site="lax",
    https_only=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"^chrome-extension://.*$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
# /scan/website: Redis cache → scraper.py → ml_service.py → cache (24h) → response
app.include_router(scan.router)
app.include_router(tasks.router)
app.include_router(chat.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}


@app.get("/api/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total_scans_query = select(func.count(ScanHistory.id)).where(
        ScanHistory.user_id == current_user.id
    )
    total_scanned = (await db.execute(total_scans_query)).scalar_one()

    threats_blocked_query = select(func.count(ScanHistory.id)).where(
        ScanHistory.user_id == current_user.id,
        ScanHistory.status == ThreatStatus.SCAM,
    )
    threats_blocked = (await db.execute(threats_blocked_query)).scalar_one()

    recent_scans_query = (
        select(ScanHistory)
        .where(ScanHistory.user_id == current_user.id)
        .order_by(desc(ScanHistory.scanned_at))
        .limit(10)
    )
    recent_scans_result = (await db.execute(recent_scans_query)).scalars().all()
    recent_scans = [ScanHistoryResponse.model_validate(scan) for scan in recent_scans_result]

    return DashboardStats(
        total_scanned=total_scanned,
        threats_blocked=threats_blocked,
        recent_scans=recent_scans,
    )

async def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}
