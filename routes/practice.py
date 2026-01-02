from fastapi import APIRouter, Query
from services.practice_service import (
    get_free_practice_questions,
    get_practice_questions
)

router = APIRouter(prefix="/api/practice", tags=["Practice"])

# FREE PRACTICE (your free-practice mode)
@router.get("/free")
async def free_practice(
    section: str = Query(...),
    topic: str = Query(...)
):
    return await get_free_practice_questions(section, topic)

# PRACTICE SET QUESTIONS
@router.get("/questions")
async def practice_questions(
    section: str,
    topic: str,
    difficulty: str,
    limit: int = 15
):
    return await get_practice_questions(
        section, topic, difficulty, limit
    )
