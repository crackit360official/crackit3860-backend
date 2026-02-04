class HRService:
    def __init__(self, db):
        self.questions = db.hr_questions
        self.progress = db.hr_progress
        self.attempts = db.hr_attempts

    async def get_questions(self):
        cursor = self.questions.find({})
        return [
            {
                "id": str(q["_id"]),
                "category": q["category"],
                "question": q["question"],
                "tips": q.get("tips", []),
                "sampleAnswer": q.get("sampleAnswer", ""),
                "keyPoints": q.get("keyPoints", []),
                "difficulty": q.get("difficulty", "Easy"),
                "commonMistakes": q.get("commonMistakes", [])
            }
            async for q in cursor
        ]
