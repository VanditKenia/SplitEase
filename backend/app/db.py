from collections.abc import AsyncIterator
from typing import Any
from uuid import uuid4

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

# Supabase's transaction pooler (Supavisor) listens on 6543; the session pooler on 5432.
TRANSACTION_POOLER_PORT = 6543


def connect_args_for(database_url: str) -> dict[str, Any]:
    """asyncpg options. A transaction pooler can hand each transaction a different server
    connection, so prepared statements must not be cached or reuse names."""
    if make_url(database_url).port != TRANSACTION_POOLER_PORT:
        return {}
    return {
        "statement_cache_size": 0,
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
    }


_database_url = get_settings().database_url
# Creating the engine doesn't connect; the first query does.
engine = create_async_engine(
    _database_url, pool_pre_ping=True, connect_args=connect_args_for(_database_url)
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one session per request, closed when the request ends."""
    async with SessionLocal() as session:
        yield session
