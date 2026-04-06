"""
Seed script: creates the initial agency and admin user.

Usage:
    cd backend
    python -m scripts.seed
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from app.database import async_session, engine, Base
from app.models.agency import Agency
from app.models.user import User
from app.core.auth import hash_password
import app.models  # noqa: F401 — register all models


AGENCY_NAME = "My Agency"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "changeme123"
ADMIN_NAME = "Admin"
DEFAULT_JOB_TITLES = [
    "Influencer Partnerships Manager",
    "Influencer Relations Manager",
    "Influencer Marketing Manager",
    "Influencer Marketing Coordinator",
    "Creator Partnerships Manager",
    "Creator Relations Manager",
    "Head of Influencer Marketing",
    "Head of Creator Partnerships",
    "Director of Influencer Marketing",
    "Director of Influencer Partnerships",
    "VP of Influencer Marketing",
    "Talent Partnerships Manager",
]


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        result = await session.execute(select(User).where(User.email == ADMIN_EMAIL))
        if result.scalar_one_or_none():
            print(f"User {ADMIN_EMAIL} already exists. Skipping seed.")
            return

        agency = Agency(name=AGENCY_NAME, target_job_titles=DEFAULT_JOB_TITLES)
        session.add(agency)
        await session.flush()

        user = User(
            agency_id=agency.id,
            email=ADMIN_EMAIL,
            hashed_password=hash_password(ADMIN_PASSWORD),
            full_name=ADMIN_NAME,
            role="admin",
        )
        session.add(user)
        await session.commit()

        print(f"Seeded agency: {AGENCY_NAME}")
        print(f"Seeded admin:  {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print("Change the password after first login!")


if __name__ == "__main__":
    asyncio.run(seed())
