from pydantic import BaseModel, Field
from typing import List, Dict
from enum import Enum
from datetime import datetime


class PerformanceRating(str, Enum):
    BEGINNER = "beginner"        # <60%
    INTERMEDIATE = "intermediate"  # 60–74%
    ADVANCED = "advanced"        # 75–89%
    EXPERT = "expert"            # ≥90%


class StreakData(BaseModel):
    current: int
    max: int
    days: List[str]


class TopicData(BaseModel):
    name: str
    accuracy: float = Field(..., ge=0, le=100)
    questions: int
    avg_time_per_question: float
    difficulty_trend: Dict[str, float]
    improvement_score: float


class AnalyticsOverview(BaseModel):
    total_questions: int
    accuracy: float
    efficiency_score: float
    consistency_score: float
    streak: StreakData
    percentile_rank: float
    performance_rating: PerformanceRating
    weakest_topic: str
    recommendations: List[str]


class AnalyticsResponse(BaseModel):
    overview: AnalyticsOverview
    topics: List[TopicData]
    time_series: List[Dict[str, float]]
