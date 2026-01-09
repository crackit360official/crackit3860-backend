from fastapi import APIRouter, Query, Depends, Request, HTTPException
from typing import List
from prometheus_client import Counter, Histogram
from services.practice_service import get_practice_questions
from services.common import normalize_difficulty
from security import get_current_user, check_rate_limit
from schemas.models import SpeedTestQuestion
import time

router = APIRouter(prefix="/api/speed-test", tags=["Speed Test"])

SPEED_HITS = Counter(
    "speed_test_hits_total",
    "Speed test usage",
    ["endpoint", "status"]
)

SPEED_LATENCY = Histogram(
    "speed_test_latency_seconds",
    "Speed test latency",
    ["endpoint"]
)

@router.get("/time-limit")
async def get_time_limit(
    level: str = Query(...),
    questions: int = Query(..., ge=1, le=50)
):
    rules = {"Easy": 60, "Medium": 45, "Hard": 30}
    return rules[normalize_difficulty(level)] * questions

@router.get("/questions", response_model=List[SpeedTestQuestion])
async def get_speed_test_questions(
    request: Request,
    section: str = Query(...),
    topic: str = Query(...),
    level: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
    user=Depends(get_current_user)
):
    if not check_rate_limit(user["id"], "speed_test"):
        raise HTTPException(429, "Rate limit exceeded")

    start = time.time()
    try:
        result = await get_practice_questions(
            section=section,
            topic=topic,
            difficulty=level,
            limit=limit
        )
        SPEED_HITS.labels(endpoint="questions", status="success").inc()
        return result
    except Exception:
        SPEED_HITS.labels(endpoint="questions", status="error").inc()
        raise
    finally:
        SPEED_LATENCY.labels(endpoint="questions").observe(time.time() - start)
