from datetime import datetime, timedelta
from typing import Optional
import hashlib
import base64
import bcrypt as _bcrypt
from jose import JWTError, jwt
from cryptography.fernet import Fernet
from app.core.config import settings


def _prepare_password(password: str) -> bytes:
    """
    Pre-hash password with SHA-256 then base64-encode.
    SHA-256 -> 32 bytes -> base64 -> exactly 44 bytes.
    44 < 72, so bcrypt never raises the 72-byte error regardless of
    the original password length or character set.
    This also fixes the passlib 1.7.4 + bcrypt 4.x incompatibility.
    """
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(digest)  # always 44 bytes


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a stored bcrypt hash."""
    try:
        prepared = _prepare_password(plain_password)
        return _bcrypt.checkpw(prepared, hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hash a password with SHA-256 + bcrypt. Never raises 72-byte limit errors."""
    prepared = _prepare_password(password)
    hashed = _bcrypt.hashpw(prepared, _bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def _get_fernet() -> Fernet:
    """
    Return a Fernet instance from ENCRYPTION_KEY.

    Supports both:
    - Proper Fernet base64 keys
    - Arbitrary strings (derived deterministically via SHA-256)
    """
    key_str = settings.ENCRYPTION_KEY
    raw_key = key_str.encode("utf-8")

    try:
        return Fernet(raw_key)
    except Exception:
        # Dev-friendly fallback: derive a valid urlsafe base64 32-byte key
        derived_key = base64.urlsafe_b64encode(hashlib.sha256(raw_key).digest())
        return Fernet(derived_key)


def encrypt_api_key(api_key: str) -> str:
    fernet = _get_fernet()
    return fernet.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    fernet = _get_fernet()
    return fernet.decrypt(encrypted_key.encode()).decode()
