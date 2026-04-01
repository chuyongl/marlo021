from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import os, secrets
from dotenv import load_dotenv
load_dotenv(dotenv_path="../../.env")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this")
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return pwd_context.hash(password[:72])

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain[:72], hashed)

def create_access_token(data: dict, expires_minutes: int = 60 * 24) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=expires_minutes)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

def generate_secure_token() -> str:
    """Generate a random URL-safe token for one-click email approvals."""
    return secrets.token_urlsafe(32)