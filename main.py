from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from uuid import uuid4
import logging
import os
import time

# =========================================================
# Load Environment Variables
# =========================================================
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
ENV = os.getenv("ENV", "development")

# =========================================================
# Logging Configuration
# =========================================================
logger = logging.getLogger("crackit360")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

file_handler = logging.FileHandler("crackit360.log")
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

# =========================================================
# Initialize FastAPI App
# =========================================================
app = FastAPI(
    title="CrackIt360 Backend",
    description="FastAPI backend powering CrackIt360",
    version="1.0",
)

# =========================================================
# Global CORS
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
# Exception Handler (422 Validation Errors)
# =========================================================
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    if ENV == "development":
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

# =========================================================
# Middlewares
# =========================================================
@app.middleware("http")
async def remove_strict_headers(request: Request, call_next):
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
    except Exception:
        process_time = (time.time() - start_time) * 1000
        logger.exception(
            f"{request.method} {request.url.path} | ERROR | {process_time:.2f}ms"
        )
        raise

    process_time = (time.time() - start_time) * 1000
    logger.info(
        f"{request.method} {request.url.path} "
        f"| {response.status_code} | {process_time:.2f}ms"
    )
    return response


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

# =========================================================
# MongoDB Connection (GLOBAL & SAFE)
# =========================================================
try:
    client = AsyncIOMotorClient(MONGO_URL)
    db = client.crackit360
    print("✅ MongoDB connected:", MONGO_URL)
except Exception as e:
    print("❌ MongoDB connection failed:", e)
    db = None

# =========================================================
# Health / Readiness Checks
# =========================================================
@app.get("/ready")
async def readiness():
    if not db:
        return {"status": "db-not-ready"}
    await db.command("ping")
    return {"status": "ready"}


@app.get("/")
async def root():
    return {
        "message": "🚀 CrackIt360 Backend Running Successfully",
        "frontend_connected": FRONTEND_URL,
        "database_connected": db is not None,
        "secret_loaded": bool(SECRET_KEY),
    }

# =========================================================
# Routers
# =========================================================
from routes import quiz, auth
from routes.technical.technical import router as technical_router, add_cors as technical_cors
from routes.practice import router as practice_router
from routes.speed_test import router as speed_test_router
from routes.discussion_router import router as discussion_router
from routes.analytics import router as analytics_router
from routes.attempts import router as attempt_router
from routes.hr import router as hr_router


app.include_router(analytics_router)
technical_cors(app)
app.include_router(quiz.router)
app.include_router(auth.router)
app.include_router(discussion_router)
app.include_router(technical_router)
app.include_router(practice_router)
app.include_router(attempt_router)
app.include_router(speed_test_router)
app.include_router(hr_router)
# =========================================================
# Serve React Build (Optional)
# =========================================================
frontend_dir = os.path.join(os.path.dirname(__file__), "../frontend/build")

if os.path.exists(frontend_dir):
    app.mount("/app", StaticFiles(directory=frontend_dir, html=True), name="frontend")

    @app.get("/app/{path:path}")
    async def serve_react_app(path: str):
        index_file = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"error": "React build not found"}

# =========================================================
# Global OPTIONS (CORS Preflight)
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
