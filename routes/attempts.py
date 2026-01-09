from fastapi import APIRouter, Depends, Request
from schemas.attempt_sc import AttemptCreate
from services.attempt_service import AttemptService
from db import db
from slowapi import Limiter
from slowapi.util import get_remote_address
import logging

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

router = APIRouter(prefix="/attempt", tags=["Attempts"])


@router.post(
    "/",
    status_code=201,
    dependencies=[Depends(limiter.limit("10/minute"))],
)
async def submit_attempt(
    request: Request,
    payload: AttemptCreate,
):
    service = AttemptService(db)

    try:
        return await service.save_attempt(payload)
    except Exception as exc:
        logger.error(
            "Attempt submission failed",
            extra={"user_id": payload.user_id, "error": str(exc)},
        )
        raise
