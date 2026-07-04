from fastapi import APIRouter, HTTPException, status

from src.data.clients import postgress_client

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/database", status_code=status.HTTP_200_OK)
async def database_health_check() -> dict[str, str]:
    if postgress_client.SessionLocal is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is not initialized",
        )

    try:
        async with postgress_client.SessionLocal() as session:
            connection = await session.connection()
            await connection.exec_driver_sql("SELECT 1")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection is unavailable",
        ) from exc

    return {"status": "ok", "database": "connected"}
