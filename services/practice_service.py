from db import db
from typing import List

# FREE PRACTICE
async def get_free_practice_questions(section: str, topic: str):
    cursor = db.questions.find(
        {"section": section, "topic": topic},
        {"_id": 0}
    )
    return await cursor.to_list(length=1000)

# PRACTICE SET QUESTIONS (Timed / Speed / Advanced)
async def get_practice_questions(
    section: str,
    topic: str,
    difficulty: str,
    limit: int
):
    pipeline = [
        {
            "$match": {
                "section": section,
                "topic": topic,
                "difficulty": difficulty
            }
        },
        {"$sample": {"size": limit}}
    ]

    cursor = db.questions.aggregate(pipeline)
    return await cursor.to_list(length=limit)
