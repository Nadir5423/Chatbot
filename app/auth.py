import datetime as dt

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import JWT_SECRET

bearer = HTTPBearer()
FILE_LINK_HOURS = 6


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user_id: str) -> str:
    """Login token (7 days)."""
    payload = {
        "sub": str(user_id),
        "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=7),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> str:
    """Returns the user id from the login token, or 401."""
    try:
        data = jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token. Please log in again.")
    if data.get("scope"):  # file-link tokens must never work as a login
        raise HTTPException(401, "Invalid or expired token. Please log in again.")
    return data["sub"]


def create_file_token(user_id: str, document_id: str) -> str:
    """Short-lived token that can only open ONE document (used in reference links)."""
    payload = {
        "sub": str(user_id),
        "doc": str(document_id),
        "scope": "file",
        "exp": dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=FILE_LINK_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def verify_file_token(token: str, document_id) -> str:
    """Returns the user id if the token is a valid file token for this document."""
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "This link has expired. Reload the chat to get a new one.")
    if data.get("scope") != "file" or data.get("doc") != str(document_id):
        raise HTTPException(403, "This link does not match this document.")
    return data["sub"]