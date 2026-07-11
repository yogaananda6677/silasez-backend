"""
JWT Helper
Tahap Login
"""
from jose import JWTError, jwt

from app.core.config import settings


def decode_access_token(token: str) -> dict:
    """
    Decode dan verifikasi JWT.
    Raise JWTError kalau token invalid/expired.
    """
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )