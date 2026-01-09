from db import quantitative_collection

# =========================
# FREE PRACTICE QUESTIONS
# =========================
async def get_free_practice_questions(section: str, topic: str):
    """
    Returns up to 1000 free practice questions for a given topic.
    """
    cursor = quantitative_collection.find(
        {"topic": topic},
        {"_id": 0}
    )
    return await cursor.to_list(length=1000)


# =========================================
# PRACTICE SET QUESTIONS (Timed / Advanced)
# =========================================
async def get_practice_questions(
    section: str,
    topic: str,
    difficulty: str,
    limit: int
):
    """
    Returns randomized practice questions based on difficulty.
    """
    pipeline = [
        {
            "$match": {
                "topic": topic,
                "difficulty": difficulty.capitalize()
            }
        },
        {
            "$sample": {
                "size": limit
            }
        }
    ]

    cursor = quantitative_collection.aggregate(pipeline)
    return await cursor.to_list(length=limit)
