import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ScanJobStatus(str, enum.Enum):
    """Redis / API workflow state for in-flight website scans."""

    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ScanType(str, enum.Enum):
    EMAIL = "email"
    WEBSITE = "website"


class ThreatStatus(str, enum.Enum):
    SAFE = "safe"
    SCAM = "scam"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    google_sub: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    picture_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    google_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    scan_history: Mapped[list["ScanHistory"]] = relationship(back_populates="user")


class ScanHistory(Base):
    __tablename__ = "scan_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[ScanType] = mapped_column(Enum(ScanType, name="scan_type", values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
    status: Mapped[ThreatStatus] = mapped_column(Enum(ThreatStatus, name="threat_status", values_callable=lambda x: [e.value for e in x]), nullable=False)
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True, index=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="scan_history")
