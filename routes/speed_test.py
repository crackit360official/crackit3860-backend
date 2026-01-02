from fastapi import APIRouter, Query

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
