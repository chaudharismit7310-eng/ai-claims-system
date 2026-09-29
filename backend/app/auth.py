from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
from passlib.context import CryptContext
from app.config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the stored bcrypt hash."""
    if len(hashed_password) == 64 and not hashed_password.startswith("$2"):
        import hashlib
        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
    try:
        pwd_bytes = plain_password.encode('utf-8')[:72]
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode('utf-8'))
    except Exception:
        return False

def hash_password(password: str) -> str:
    """Generate a secure bcrypt hash for a plain password."""
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

# Alias for backward compatibility if any route calls get_password_hash
get_password_hash = hash_password

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Generate a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None