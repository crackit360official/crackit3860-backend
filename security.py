import os
import re
import bcrypt
import hashlib
import secrets
import mimetypes
import pathlib
from datetime import datetime, timedelta
from typing import Dict, Any, Mapping, Optional, Iterable
from collections import defaultdict

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from bson import ObjectId
from jose import jwt, JWTError

from db import user_collection

# ============================================================
# 🔧 Load Environment Variables
# ============================================================
load_dotenv()


def require_env(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


SECRET_KEY = require_env("SECRET_KEY")
JWT_ALGORITHM = require_env("JWT_ALGORITHM")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)

REFRESH_TOKEN_EXPIRE_DAYS = int(
    os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")
)

EMAIL_SALT = require_env("EMAIL_SALT")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# ============================================================
# 🔐 Password Hashing
# ============================================================
def hash_password(password: str) -> str:
    if not isinstance(password, str):
        raise TypeError("Password must be a string")

    password_bytes = password.strip().encode("utf-8")

    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        plain_bytes = plain_password.strip().encode("utf-8")
        if len(plain_bytes) > 72:
            plain_bytes = plain_bytes[:72]
        return bcrypt.checkpw(plain_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False


# ============================================================
# 🔑 JWT Access Tokens
# ============================================================
def create_access_token(
    subject: str,
    extra: Optional[Dict[str, Any]] = None,
    expires_minutes: Optional[int] = None
) -> str:
    payload = {"sub": subject}

    if extra:
        payload.update(extra)

    expire = datetime.utcnow() + timedelta(
        minutes=expires_minutes or ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload["exp"] = expire

    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])

        if "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


def get_token_subject(token: str) -> str:
    payload = decode_access_token(token)
    return payload["sub"]


# ============================================================
# 🔁 Refresh Token Handling
# ============================================================
def create_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ============================================================
# 🧱 MongoDB Injection Protection
# ============================================================
def safe_object_id(id_str: str) -> ObjectId:
    if not ObjectId.is_valid(id_str):
        raise HTTPException(status_code=400, detail="Invalid ID format")
    return ObjectId(id_str)


def escape_regex(text: str) -> str:
    return re.escape(str(text))


def build_safe_filter(
    client_filter: Mapping[str, Any],
    allowed_fields: Iterable[str]
) -> Dict[str, Any]:
    safe = {}

    for key, value in (client_filter or {}).items():
        if key not in allowed_fields or key.startswith("$"):
            continue
        if isinstance(value, dict):
            raise HTTPException(status_code=400, detail="Invalid filter value")
        safe[key] = value

    return safe


def build_update_payload(
    body: Mapping[str, Any],
    allowed_fields: Iterable[str]
) -> Dict[str, Any]:
    safe_update = {}

    for key, value in (body or {}).items():
        if key not in allowed_fields or key.startswith("$"):
            continue
        if isinstance(value, dict):
            raise HTTPException(status_code=400, detail="Invalid update value")
        safe_update[key] = value

    if not safe_update:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    return {"$set": safe_update}


# ============================================================
# 🧩 File Upload Protection
# ============================================================
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf", ".txt"}
ALLOWED_MIME_PREFIXES = ("image/", "text/", "application/pdf")

UPLOAD_TMP_DIR = os.getenv("UPLOAD_TMP_DIR", "./uploads/tmp")
os.makedirs(UPLOAD_TMP_DIR, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    name = pathlib.Path(filename).name
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)


def validate_upload(file_stream, filename: str):
    safe_name = sanitize_filename(filename)
    ext = pathlib.Path(safe_name).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File type not allowed")

    file_path = os.path.join(
        UPLOAD_TMP_DIR, f"{secrets.token_hex(8)}_{safe_name}"
    )

    size = 0
    with open(file_path, "wb") as f:
        while chunk := file_stream.read(4096):
            size += len(chunk)
            if size > MAX_UPLOAD_SIZE:
                f.close()
                os.remove(file_path)
                raise HTTPException(status_code=400, detail="File too large")
            f.write(chunk)

    guessed_mime, _ = mimetypes.guess_type(file_path)
    if guessed_mime and not guessed_mime.startswith(ALLOWED_MIME_PREFIXES):
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="Suspicious file type")

    file_hash = hashlib.sha256(open(file_path, "rb").read()).hexdigest()

    return {"path": file_path, "size": size, "hash": file_hash}


# ============================================================
# 🧠 Phishing Detection
# ============================================================
URL_RE = re.compile(r"https?://[^\s]+")


def detect_phishing_links(text: str) -> Dict[str, Any]:
    urls = URL_RE.findall(text or "")
    suspicious = [
        u for u in urls if "@" in u or u.count("//") > 1 or len(u) > 250
    ]
    return {"found": len(urls), "suspicious": suspicious}


# ============================================================
# ⏱️ Simple Rate Limiter
# ============================================================
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "30"))

_rate_store = defaultdict(list)


def check_rate_limit(ip: str, route: str) -> bool:
    now = datetime.utcnow().timestamp()
    key = f"{ip}:{route}"

    _rate_store[key] = [
        t for t in _rate_store[key] if now - t < RATE_LIMIT_WINDOW
    ]

    if len(_rate_store[key]) >= RATE_LIMIT_MAX:
        return False

    _rate_store[key].append(now)
    return True


# ============================================================
# 🔒 Password Reset Tokens
# ============================================================
def create_reset_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=15)
    payload = {
        "sub": email,
        "purpose": "reset_password",
        "exp": expire
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_reset_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])

        if payload.get("purpose") != "reset_password":
            raise HTTPException(status_code=400, detail="Invalid token purpose")

        return payload["sub"]

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired reset token"
        )


# ============================================================
# 👤 Current User Dependency
# ============================================================
async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)

    user_id = payload.get("sub")
    user_name = payload.get("name")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    if not user_name:
        user = await user_collection.find_one(
            {"_id": ObjectId(user_id)},
            {"name": 1}
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        user_name = user.get("name")

    return {
        "id": str(user_id),
        "name": user_name
    }
