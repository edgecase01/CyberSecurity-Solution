#!/usr/bin/env python3
"""
Initialize or migrate the database to the latest multi-tenant schema.

Usage (from backend/):
  python scripts/init_db.py
  python scripts/init_db.py --reset   # drop all tables, then migrate (local dev only)
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import create_async_engine

from config import get_settings
from models import Base


def run_alembic_upgrade() -> None:
    alembic_cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    command.upgrade(alembic_cfg, "head")


async def reset_database() -> None:
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Alembic migrations for Cybersec backend.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop all SQLAlchemy tables before migrating (destructive; dev only).",
    )
    args = parser.parse_args()

    if args.reset:
        print("Dropping all tables…")
        asyncio.run(reset_database())

    print("Applying Alembic migrations…")
    run_alembic_upgrade()
    print("Database is up to date (revision: head).")


if __name__ == "__main__":
    main()
