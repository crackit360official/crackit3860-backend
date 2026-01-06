from pydantic import BaseModel, Field, validator
from datetime import datetime


class AttemptCreate(BaseModel):
    attempt_id: str
    user_id: str
    question_id: str
    topic: str
    difficulty: str = Field("medium", regex="^(easy|medium|hard)$")
    is_correct: bool
    time_spent: float
    created_at: datetime | None = None

    @validator("topic")
    def validate_topic(cls, v):
        banned = {"admin", "system", "<script>"}
        if any(b in v.lower() for b in banned):
            raise ValueError("Invalid topic")
        return v
