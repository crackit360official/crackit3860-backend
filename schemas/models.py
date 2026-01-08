from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Any, Dict, Literal
from datetime import datetime

# =========================================================
# ATTEMPT MODELS
# =========================================================

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
    created_at: Optional[datetime] = None

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str):
        banned = {"admin", "system", "<script>"}
        if any(b in v.lower() for b in banned):
            raise ValueError("Invalid topic")
        return v


class PracticeQuery(BaseModel):
    topic: str = Field(min_length=2)
    difficulty: str = Field(
        default="medium",
        pattern="^(easy|medium|hard)$"
    )
    limit: int = Field(default=10, ge=1, le=50)
    skip: int = Field(default=0, ge=0)

    class Config:
        extra = "forbid"


# =========================================================
# USER MODELS
# =========================================================

class UserBase(BaseModel):
    name: str
    email: EmailStr


class EmailRequest(BaseModel):
    user_email: str


class UserRegister(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserInDB(UserBase):
    id: Optional[str] = Field(default=None, alias="_id")
    password: str
    email_verified: bool = False
    refresh_tokens: Optional[List[dict]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# =========================================================
# AUTH RESPONSE MODELS
# =========================================================

class AuthUser(BaseModel):
    id: str
    name: str
    email: EmailStr
    auth_provider: str
    avatar: Optional[str] = ""


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUser


class MessageOnly(BaseModel):
    message: str


class PasswordResetResponse(BaseModel):
    message: str


# =========================================================
# PROFILE
# =========================================================

class Profile(BaseModel):
    name: str
    age: int


class MessageResponse(BaseModel):
    message: str
    data: Optional[Any] = None


# =========================================================
# QUIZ SUBMISSION
# =========================================================

class QuizSubmissionPayload(BaseModel):
    userId: str
    userTrack: str
    answers: List[Optional[int]]
    timeTaken: int


class DailyQuizStudent(BaseModel):
    user_id: str
    user_name: str
    user_email: str
    track: str
    question_ids: List[str]
    selected_answers: List[int]
    correct_answers: List[int]
    score: float
    accuracy: float
    total_questions: int
    time_taken: int
    date: datetime = Field(default_factory=datetime.utcnow)


# =========================================================
# TECHNICAL QUESTIONS
# =========================================================

class Question(BaseModel):
    id: str
    title: str
    difficulty: str
    category: str
    description: str
    inputFormat: str
    outputFormat: str
    sampleInput: str
    sampleOutput: str
    explanation: str
    constraints: Optional[str]
    templates: Dict[str, str]


# =========================================================
# QUANTITATIVE
# =========================================================

class SpeedTestQuestion(BaseModel):
    id: str
    question: str
    options: List[str]
    correctAnswer: str
    topic: str
    level: str
    difficulty: Optional[str] = None


class SubmitRequest(BaseModel):
    user_id: Optional[str]
    topic: str
    level: str
    answers: List[int]


# =========================================================
# DISCUSSION
# =========================================================

class DiscussionCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    content: str = Field(..., min_length=10)
    category: str


class ReplyCreate(BaseModel):
    discussionId: str
    content: str


class VoteCreate(BaseModel):
    type: Literal["UPVOTE", "DOWNVOTE"]


# =========================================================
# FREE PRACTICE
# =========================================================

class QuestionOut(BaseModel):
    section: str
    stage: str
    topic: str
    difficulty: str
    question: str
    options: List[str]
    correctAnswer: str
    solution: Optional[str]


class QuestionAttempt(BaseModel):
    user_id: str
    question_id: str
    topic: str
    is_correct: bool
    time_spent: float
    created_at: datetime = Field(default_factory=datetime.utcnow)
