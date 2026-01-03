from fastapi import APIRouter, Query
from services.practice_service import (
    get_free_practice_questions,
    get_practice_questions
)

router = APIRouter(prefix="/api/practice", tags=["Practice"])

@router.get("/free")
async def free_practice(
    section: str = Query(...),
    topic: str = Query(...)
):
    return await get_free_practice_questions(section, topic)


@router.get("/questions")
async def practice_questions(
    section: str = Query(...),
    topic: str = Query(...),
    difficulty: str = Query(...),
    limit: int = Query(10)
):
    return await get_practice_questions(
        section=section,
        topic=topic,
        difficulty=difficulty,
        limit=limit
    )
