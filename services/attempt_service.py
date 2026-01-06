from schemas.attempt import AttemptCreate
from fastapi import HTTPException
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AttemptService:
    def __init__(self, db):
        self.collection = db.question_attempts

    async def save_attempt(self, data: AttemptCreate):
        try:
            payload = data.model_dump(exclude_none=True)
            payload.setdefault("created_at", datetime.utcnow())

            await self.collection.replace_one(
                {"attempt_id": data.attempt_id},
                payload,
                upsert=True,
            )
            return {"status": "saved"}
        except Exception as exc:
            logger.exception(
                "Failed to save attempt",
                extra={"attempt_id": data.attempt_id},
            )
            raise HTTPException(
                status_code=500, detail="Attempt save failed"
            )
