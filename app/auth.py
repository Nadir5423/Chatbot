import datetime as dt

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import JWT_SECRET

bearer = HTTPBearer()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user_id: str) -> str:
    payload = {
        "sub": str(user_id),
        "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=7),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    """Returns the user id from the token, or 401."""
    try:
        data = jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])
        return data["sub"]
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token. Please log in again.")