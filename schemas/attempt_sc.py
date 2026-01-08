from pydantic import BaseModel, Field,  field_validator
from datetime import datetime
class AttemptCreate(BaseModel):
    attempt_id: str
    user_id: str
    question_id: str
    topic: str
    difficulty: str = Field(
        default="medium",
        pattern="^(easy|medium|hard)$"
    )
    is_correct: bool
    time_spent: float
    created_at: datetime | None = None

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str):
        banned = {"admin", "system", "<script>"}
        if any(b in v.lower() for b in banned):
            raise ValueError("Invalid topic")
        return v
def validate_topic(cls, v): 
    banned = {"admin", "system", "<script>"} 
    if any(b in v.lower() for b in banned): 
        raise ValueError("Invalid topic") 
    return v