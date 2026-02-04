from pydantic import BaseModel
from typing import List

class HRQuestionOut(BaseModel):
    id: str
    category: str
    question: str
    tips: List[str]
    sampleAnswer: str
    keyPoints: List[str]
    difficulty: str
    commonMistakes: List[str]

class HRProgressOut(BaseModel):
    completed_questions: List[str]
    progress_percentage: float
    total_time_spent: int

class HRAttemptCreate(BaseModel):
    question_id: str
    duration: int
