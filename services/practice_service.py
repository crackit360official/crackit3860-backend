from db import quantitative_collection
from typing import List

# FREE PRACTICE
async def get_free_practice_questions(section: str, topic: str):
    cursor = quantitative_collection.find(
        {"topic": topic},
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
                "topic": topic,
                "difficulty": difficulty.capitalize()
            }
        },
        {"$sample": {"size": limit}}
    ]

    cursor = quantitative_collection.aggregate(pipeline)
    return await cursor.to_list(length=limit)

