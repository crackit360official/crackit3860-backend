from db import quantitative_collection
from services.common import normalize_difficulty
from redis.asyncio import Redis
import json

redis = Redis(
    host="localhost",
    port=6379,
    db=0,
    max_connections=50,
    retry_on_timeout=True,
    decode_responses=True
)

# ---------------- INDEX CREATION ----------------
async def create_indexes():
    await quantitative_collection.create_index(
        [("topic", 1)], name="topic_index"
    )
    await quantitative_collection.create_index(
        [("topic", 1), ("difficulty", 1)],
        name="topic_difficulty"
    )

# ---------------- FREE PRACTICE ----------------
async def get_free_practice_questions(
    topic: str,
    skip: int = 0,
    limit: int = 20
):
    cache_key = f"free:{topic}:{skip}:{limit}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    pipeline = [
        {"$match": {"topic": topic}},
        {"$hint": "topic_index"},
        {"$skip": skip},
        {"$limit": limit}
    ]

    cursor = quantitative_collection.aggregate(pipeline)
    result = await cursor.to_list(length=limit)

    await redis.setex(cache_key, 300, json.dumps(result))
    return result

# ---------------- PRACTICE / SPEED ----------------
async def get_practice_questions(
    section: str,
    topic: str,
    difficulty: str,
    limit: int
):
    cache_key = f"practice:{topic}:{difficulty}:{limit}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    pipeline = [
        {
            "$match": {
                "topic": topic,
                "difficulty": normalize_difficulty(difficulty)
            }
        },
        {"$hint": "topic_difficulty"},
        {"$limit": 200},
        {"$sample": {"size": limit}}
    ]

    cursor = quantitative_collection.aggregate(pipeline)
    result = await cursor.to_list(length=limit)

    await redis.setex(cache_key, 300, json.dumps(result))
    return result
