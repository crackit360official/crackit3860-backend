from fastapi import FastAPI, HTTPException ,Request
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import logging
import os
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
import time
from uuid import uuid4
from fastapi.responses import JSONResponse, FileResponse

# =========================================================
# ✅Load Environment Variables
# =========================================================
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# =========================================================
# ✅Logging
# =========================================================
logger = logging.getLogger("CrackIt360")
logging.basicConfig(level=logging.INFO)
logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)
# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
# File handler
file_handler = logging.FileHandler("crackit360.log")
file_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# =========================================================
# Initialize FastAPI App
# =========================================================
app = FastAPI(
    title="CrackIt360 Backend",
    description="FastAPI backend powering CrackIt360",
    version="1.0",
)

# =========================================================
# Global CORS (PRIMARY)
# =========================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# =========================================================
# Validation Error Debugger
# =========================================================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.error(f"422 Validation Error | {request.url.path} | {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )
# ===============================
# 422 VALIDATION ERROR DEBUGGER
# ===============================
print("🔹 Login request received")
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    if os.getenv("ENV") == "development":
        print("\n===== 422 VALIDATION ERROR =====")
        print("PATH:", request.url.path)
        print("ERRORS:", exc.errors())
        try:
            body = await request.body()
            print("BODY:", body.decode() if body else "EMPTY")
        except Exception:
            pass
        print("===============================\n")
    else:
        logger.error(
            f"422 Validation Error | PATH={request.url.path} | ERRORS={exc.errors()}"
        )

    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )
@app.get("/ready")
async def readiness():
    await db.command("ping")
    return {"status": "ready"}
# =========================================================
# ✅ CORS Configuration (Allow Frontend Requests)
# =========================================================

@app.middleware("http")
async def remove_strict_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
    response.headers["Cross-Origin-Embedder-Policy"] = "unsafe-none"
    return response

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = str(uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = time.time()

    try:
        response = await call_next(request)
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.exception(
            f"{request.method} {request.url.path} "
            f"| ERROR | {process_time:.2f}ms"
        )
        raise

    process_time = (time.time() - start_time) * 1000

    logger.info(
        f"{request.method} {request.url.path} "
        f"| {response.status_code} | {process_time:.2f}ms"
    )

    return response

# Optional Practice CORS (from GitHub)
# =========================================================
@app.middleware("http")
async def force_practice_cors(request: Request, call_next):
    response = await call_next(request)

    if request.url.path.startswith("/api/practice"):
        origin = request.headers.get("origin")
        if origin in ("http://localhost:3000", "http://127.0.0.1:3000"):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "*"

    return response



# Import internal modules
from routes import quiz, auth
from schemas.models import Profile
from routes.technical.technical import router as technical_router, add_cors as technical_cors
from routes.practice import router as practice_router
from routes.speed_test import router as speed_test_router
from routes.discussion_router import router as discussion_router
from routes.analytics import router as analytics_router
from routes.attempts import router as attempt_router
from routes.hr import router as hr_router

app.include_router(auth.router)
app.include_router(quiz.router)
technical_cors(app)
app.include_router(technical_router)
app.include_router(discussion_router)
app.include_router(practice_router)
app.include_router(speed_test_router)
app.include_router(attempt_router)
app.include_router(analytics_router)
app.include_router(hr_router)
# =========================================================
# ✅ MongoDB Connection
# =========================================================
try:
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.crackit360
    print("✅ MongoDB connected successfully:", MONGO_URL)
except Exception as e:
    print("❌ MongoDB connection failed:", e)
    db = None
# ========================================================
# ✅ Simple Profile API Example
# =========================================================
@app.post("/api/profile")
async def create_profile(profile: Profile):
    """
    Example endpoint to test MongoDB connectivity.
    """
    if not db:
        raise HTTPException(status_code=500, detail="Database not connected")

    data = {"name": profile.name, "age": profile.age}
    result = await db.profile.insert_one(data)

    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Failed to insert profile")

    return {"message": "Profile added successfully", "id": str(result.inserted_id)}


# =========================================================
# ✅ Serve React Frontend Build (if exists)
# =========================================================
frontend_dir = os.path.join(os.path.dirname(__file__), "../frontend/build")

if os.path.exists(frontend_dir):
    app.mount("/app", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    @app.get("/app/{path_name:path}")
    async def serve_react_app(path_name: str):
        index_file = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"error": "React build not found"}
# =========================================================
# ✅ Root Route (Health Check)
# =========================================================
@app.get("/")
async def root():
    return {
        "message": "🚀 CrackIt360 Backend Running Successfully",
        "frontend_connected": FRONTEND_URL,
        "database_connected": db is not None,
        "secret_loaded": bool(SECRET_KEY),
    }


# =========================================================
# ✅ Register MongoDB Lifecycle Events
# =========================================================
@app.options("/{path:path}")
async def global_preflight(path: str, request: Request):
    response = JSONResponse(status_code=200, content={})
    origin = request.headers.get("origin")

    if origin in ("http://localhost:3000", "http://127.0.0.1:3000"):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"

    return response
