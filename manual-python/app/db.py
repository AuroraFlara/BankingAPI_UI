"""Database setup: async SQLAlchemy engine and session factory.

This module creates the engine using `DATABASE_URL` from `.env` and
exposes `get_db` as a dependency for routes.
"""

import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "mysql+asyncmy://root:password@127.0.0.1:3306/bankingapp_new"
)

# Prefer asyncmy, fall back to aiomysql if available. Provide a clear error if neither is installed.
engine = None
last_error = None
for driver in ("asyncmy", "aiomysql"):
    try:
        if f"+{driver}" in DATABASE_URL or driver == "asyncmy":
            test_url = DATABASE_URL
            if f"+{driver}" not in DATABASE_URL and "+asyncmy" in DATABASE_URL:
                test_url = DATABASE_URL.replace("+asyncmy", f"+{driver}")
            engine = create_async_engine(test_url, pool_pre_ping=True)
            break
    except Exception as e:
        last_error = e

if engine is None:
    raise RuntimeError(
        "No async MySQL driver available. Install 'asyncmy' or 'aiomysql' in your venv (pip install asyncmy or pip install aiomysql)."
    )

AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
