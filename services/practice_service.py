from db import quantitative_collection

# ---------------- FREE PRACTICE ----------------
async def get_free_practice_questions(
    topic: str,
    skip: int,
    limit: int
):
    cursor = quantitative_collection.find(
        {"topic": topic},
        {"_id": 0}
    ).skip(skip).limit(limit)

    return await cursor.to_list(length=limit)


# ---------------- AUTH PRACTICE ----------------
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
                "difficulty": difficulty.capitalize()
            }
        },
        {"$sample": {"size": limit}}
    ]

    cursor = quantitative_collection.aggregate(pipeline)
    return await cursor.to_list(length=limit)
