# db.py
import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from fastapi import FastAPI
from dotenv import load_dotenv
import certifi

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME", "crackit360")

# ----------------------------------------------------
# MongoDB Atlas connection
# ----------------------------------------------------
client = AsyncIOMotorClient(
    MONGO_URL,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=30000
)

db = client[DB_NAME]

# ----------------------------------------------------
# Dependency helpers
# ----------------------------------------------------
def get_db():
    return db

def get_fs_bucket() -> AsyncIOMotorGridFSBucket:
    return AsyncIOMotorGridFSBucket(db, bucket_name="hr_audio")

# ----------------------------------------------------
# Collections
# ----------------------------------------------------
user_collection = db["User_details"]
quiz_collection = db["DailyQuizQuestions"]
quiz_student_collection = db["DailyQuizStudent"]
profile_collection = db["profile"]

technical_questions = db["TechnicalQuestions"]
technical_submissions = db["TechnicalSubmissions"]

discussion_col = db["Discussion"]
reply_col = db["Discussion_replies"]
vote_col = db["vote_col"]

# HR module
hr_questions = db["hr_questions"]
hr_progress = db["hr_progress"]
hr_attempts = db["hr_attempts"]

# Quantitative / speed test
quantitative_collection = db["QuantitativeQuestions"]
speedtest_submissions = db["SpeedTestSubmissions"]

# ----------------------------------------------------
# MongoDB health check
# ----------------------------------------------------
async def test_mongo_connection():
    try:
        await db.command("ping")
        print("✅ MongoDB ping successful!")
    except Exception as e:
        print("❌ MongoDB ping failed:", e)
        raise e

# ----------------------------------------------------
# Indexes
# ----------------------------------------------------
async def create_indexes():
    await user_collection.create_index("email", unique=True)
    await quiz_collection.create_index("type")
    await quiz_student_collection.create_index("user_id")
    await hr_progress.create_index("user_id")

    print("✅ MongoDB indexes created successfully.")

# ----------------------------------------------------
# FastAPI lifecycle
# ----------------------------------------------------
def setup_db_events(app: FastAPI):
    @app.on_event("startup")
    async def startup_event():
        await test_mongo_connection()
        await create_indexes()
        print("🚀 MongoDB connected and indexes ready.")

    @app.on_event("shutdown")
    async def shutdown_event():
        client.close()
        print("🛑 MongoDB connection closed.")
