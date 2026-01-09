from datetime import datetime, timedelta
import json
import statistics
import logging
from schemas.analysis_sc import (
    AnalyticsResponse,
    AnalyticsOverview,
    TopicData,
    PerformanceRating,
    StreakData,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, db):
        self.db = db
        self.collection = db.question_attempts
        self.cache = db.analytics_cache

    async def mongo_cache(self, key: str, compute_fn):
        cached = await self.cache.find_one(
            {"key": key, "expires": {"$gt": datetime.utcnow()}}
        )
        if cached:
            return AnalyticsResponse(**json.loads(cached["data"]))

        result = await compute_fn()
        await self.cache.replace_one(
            {"key": key},
            {
                "key": key,
                "data": json.dumps(result.model_dump()),
                "expires": datetime.utcnow() + timedelta(minutes=5),
            },
            upsert=True,
        )
        return result

    async def get_analytics(self, user_id: str):
        cache_key = f"analytics:{user_id}"
        return await self.mongo_cache(cache_key, lambda: self._compute(user_id))

    async def _compute(self, user_id: str):
        # ================= STREAK =================
        pipeline_streak = [
            {"$match": {"user_id": user_id, "is_correct": True}},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at",
                        }
                    },
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": -1}},
        ]
        streak_data = await self.collection.aggregate(pipeline_streak).to_list(None)

        current = 0
        max_streak = 0
        streak_days = []
        for day in streak_data:
            if day["count"] > 0:
                current += 1
                max_streak = max(max_streak, current)
                streak_days.append(day["_id"])
            else:
                break

        # ================= TOPICS =================
        pipeline_topics = [
            {"$match": {"user_id": user_id}},
            {
                "$group": {
                    "_id": "$topic",
                    "total": {"$sum": 1},
                    "correct": {"$sum": {"$cond": ["$is_correct", 1, 0]}},
                    "time": {"$sum": "$time_spent"},
                    "attempts": {"$push": "$$ROOT"},
                }
            },
        ]
        topics_raw = await self.collection.aggregate(pipeline_topics).to_list(None)

        if not topics_raw:
            return AnalyticsResponse(
                overview=AnalyticsOverview(
                    total_questions=0,
                    accuracy=0,
                    efficiency_score=0,
                    consistency_score=0,
                    streak=StreakData(current=0, max=0, days=[]),
                    percentile_rank=0,
                    performance_rating=PerformanceRating.BEGINNER,
                    weakest_topic="",
                    recommendations=[
                        "🎯 Complete 5+ questions to unlock analytics",
                        "📚 Start with easy questions",
                        "🔥 Practice daily to build streaks",
                    ],
                ),
                topics=[],
                time_series=[],
            )

        topics = []
        total_q = total_c = total_t = 0
        accuracies = []

        for t in topics_raw:
            acc = (t["correct"] / t["total"]) * 100
            avg_time = t["time"] / t["total"]

            diff = {"easy": [], "medium": [], "hard": []}
            for a in t["attempts"]:
                diff[a.get("difficulty", "medium")].append(a["is_correct"])

            diff_trend = {
                k: round(sum(v) / len(v) * 100, 1) if v else 0
                for k, v in diff.items()
            }

            topics.append(
                TopicData(
                    name=t["_id"],
                    accuracy=round(acc, 1),
                    questions=t["total"],
                    avg_time_per_question=round(avg_time, 1),
                    difficulty_trend=diff_trend,
                    improvement_score=0.0,
                )
            )

            total_q += t["total"]
            total_c += t["correct"]
            total_t += t["time"]
            accuracies.append(acc)

        accuracy = (total_c / total_q) * 100
        efficiency = (accuracy / 100) * (30 / (total_t / total_q))
        consistency = (
            round(statistics.stdev(accuracies), 2) if len(accuracies) > 1 else 0
        )

        weakest = min(topics, key=lambda x: x.accuracy).name

        rating = (
            PerformanceRating.EXPERT
            if accuracy >= 90
            else PerformanceRating.ADVANCED
            if accuracy >= 75
            else PerformanceRating.INTERMEDIATE
            if accuracy >= 60
            else PerformanceRating.BEGINNER
        )

        # ================= TIME SERIES =================
        pipeline_time = [
            {"$match": {"user_id": user_id}},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at",
                        }
                    },
                    "correct": {
                        "$sum": {"$cond": ["$is_correct", 1, 0]}
                    },
                    "total": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        ts_raw = await self.collection.aggregate(pipeline_time).to_list(None)
        time_series = [
            {
                "date": r["_id"],
                "accuracy": round((r["correct"] / r["total"]) * 100, 1),
            }
            for r in ts_raw
        ]

        overview = AnalyticsOverview(
            total_questions=total_q,
            accuracy=round(accuracy, 1),
            efficiency_score=round(efficiency, 2),
            consistency_score=consistency,
            streak=StreakData(current=current, max=max_streak, days=streak_days),
            percentile_rank=min(99.9, accuracy * 1.1),
            performance_rating=rating,
            weakest_topic=weakest,
            recommendations=[
                f"🎯 Focus on {weakest} – lowest accuracy",
                "🔥 Maintain daily practice streak",
                "⏱ Improve speed to boost efficiency",
            ],
        )

        return AnalyticsResponse(
            overview=overview, topics=topics, time_series=time_series
        )
