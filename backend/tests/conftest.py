import os

# Set before importing the app so settings never come from a real .env (no real Supabase/DB).
os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres@localhost:5432/splitease_test"
os.environ["SUPABASE_URL"] = "https://test-project.supabase.co"
os.environ["CORS_ORIGINS"] = "http://localhost:5000"
os.environ["ENV"] = "dev"

from collections.abc import AsyncIterator  # noqa: E402

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """HTTP client that calls the app in-process (no server, no network)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
