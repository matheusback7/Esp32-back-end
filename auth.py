"""
Autenticação:
- Hash de senha com PBKDF2-HMAC-SHA256 (stdlib, sem dependência de bcrypt).
- Tokens JWT para o dashboard (usuário humano).
- Verificação simples de API Key para os dispositivos ESP32.
"""
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

security = HTTPBearer()

PBKDF2_ITERATIONS = 260_000


# ---------- Hash de senha ----------
def hash_password(password: str, salt: bytes | None = None) -> str:
    """Gera 'salt_hex$hash_hex' para armazenar em ADMIN_PASSWORD_HASH."""
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_hex, digest_hex = stored_hash.split("$")
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    new_digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return hmac.compare_digest(new_digest.hex(), digest_hex)


# ---------- JWT (usuário do dashboard) ----------
def create_access_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Dependency para proteger rotas HTTP do dashboard."""
    return decode_access_token(credentials.credentials)


def authenticate_user(username: str, password: str) -> bool:
    if not settings.ADMIN_PASSWORD_HASH:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ADMIN_PASSWORD_HASH não configurado no .env",
        )
    if not secrets.compare_digest(username, settings.ADMIN_USERNAME):
        return False
    return verify_password(password, settings.ADMIN_PASSWORD_HASH)


# ---------- API Key (dispositivos ESP32) ----------
def verify_device_api_key(api_key: str) -> bool:
    return secrets.compare_digest(api_key, settings.DEVICE_API_KEY)
