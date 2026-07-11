import hashlib
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.config import settings

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# 1. NORMALIZE (hindari bcrypt 72 byte limit)
def normalize_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# 2. HASH
def hash_password(password: str) -> str:
    normalized = normalize_password(password)
    return pwd_context.hash(normalized)

# 3. VERIFY
def verify_password(plain_password: str, hashed_password: str) -> bool:
    normalized = normalize_password(plain_password)
    return pwd_context.verify(normalized, hashed_password)

# 4. JWT
def create_access_token(data: dict, expires_minutes: int | None = None) -> str:
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
