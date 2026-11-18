from httpx import AsyncClient

from app.errors import NotAllowed
from app.main import app


@app.get("/_test/not-allowed")
async def raise_not_allowed() -> None:
    raise NotAllowed("Only the owner can do this.")


@app.get("/_test/validation")
async def needs_int(limit: int) -> None:
    return None


async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_unknown_route_returns_error_format(client: AsyncClient) -> None:
    response = await client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {"error": {"code": "not_found", "message": "Not Found"}}


async def test_app_error_maps_to_status_and_code(client: AsyncClient) -> None:
    response = await client.get("/_test/not-allowed")

    assert response.status_code == 403
    assert response.json() == {
        "error": {"code": "not_allowed", "message": "Only the owner can do this."}
    }


async def test_validation_error_lists_fields(client: AsyncClient) -> None:
    response = await client.get("/_test/validation", params={"limit": "abc"})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["details"][0]["field"] == "query.limit"
