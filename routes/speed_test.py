from fastapi import APIRouter, Query
from fastapi import APIRouter, Query
from services.practice_service import get_practice_questions
router = APIRouter(prefix="/api/speed-test", tags=["Speed Test"])
router = APIRouter(prefix="/api/speed-test", tags=["Speed Test"])

@router.get("/time-limit")
async def get_time_limit(
    level: str = Query(...),
    questions: int = Query(...)
):
    """
    Simple deterministic time rule:
    - Easy: 60 sec / question
    - Intermediate: 45 sec / question
    - Hard: 30 sec / question
    """
    per_question = {
        "easy": 60,
        "intermediate": 45,
        "hard": 30
    }.get(level.lower(), 45)

    return per_question * questions

@router.get("/questions")
async def get_speed_test_questions(
    section: str = Query(...),
    topic: str = Query(...),
    level: str = Query(...),
    limit: int = 10
):
    """
    Speed Test uses same question pool as practice
    but with strict limit + randomization
    """
    return await get_practice_questions(
        section=section,
        topic=topic,
        difficulty=level,
        limit=limit
    )
