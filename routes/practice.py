from fastapi import APIRouter, Query, Depends, Request, HTTPException
from typing import List
from prometheus_client import Counter, Histogram
from services.practice_service import (
    get_free_practice_questions,
    get_practice_questions
)
from security import get_current_user, check_rate_limit
from schemas.models import PracticeQuery, QuestionOut
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/practice", tags=["Practice"])

# ---------------- METRICS ----------------
PRACTICE_HITS = Counter(
    "practice_api_hits_total",
    "Practice API usage",
    ["endpoint", "status"]
)

PRACTICE_LATENCY = Histogram(
    "practice_request_latency_seconds",
    "Practice API latency",
    ["endpoint"]
)

# ---------------- FREE PRACTICE ----------------
@router.get("/free", response_model=List[QuestionOut])
async def free_practice(
    request: Request,
    section: str = Query(...),
    topic: str = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50)
):
    client_key = f"{request.client.host}:anon"
    if not check_rate_limit(client_key, "free_practice"):
        raise HTTPException(429, "Rate limit exceeded")

    start = time.time()
    try:
        result = await get_free_practice_questions(topic, skip, limit)
        PRACTICE_HITS.labels(endpoint="free", status="success").inc()
        return result
    except Exception as e:
        PRACTICE_HITS.labels(endpoint="free", status="error").inc()
        logger.error("free_practice_failed", exc_info=True)
        raise
    finally:
        PRACTICE_LATENCY.labels(endpoint="free").observe(time.time() - start)

# ---------------- AUTH PRACTICE ----------------
@router.get("/questions", response_model=List[QuestionOut])
async def practice_questions(
    request: Request,
    query: PracticeQuery = Depends(),
    user=Depends(get_current_user)
):
    client_key = f"{request.client.host}:{user['id']}"
    if not check_rate_limit(client_key, "practice_questions"):
        raise HTTPException(429, "Rate limit exceeded")

    start = time.time()
    try:
        result = await get_practice_questions(
            section=query.section,
            topic=query.topic,
            difficulty=query.difficulty,
            limit=query.limit
        )
        PRACTICE_HITS.labels(endpoint="questions", status="success").inc()
        return result
    except Exception:
        PRACTICE_HITS.labels(endpoint="questions", status="error").inc()
        logger.error("practice_questions_failed", exc_info=True)
        raise
    finally:
        PRACTICE_LATENCY.labels(endpoint="questions").observe(time.time() - start)
