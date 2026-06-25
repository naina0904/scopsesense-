import datetime
from typing import Optional

import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

import os

# Secret key – load from environment variable JWT_SECRET
SECRET_KEY = os.environ["JWT_SECRET"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class TokenData(BaseModel):
    user_id: int
    role: str
    exp: Optional[int] = None

security = HTTPBearer()

def create_access_token(*, user_id: int, role: str, expires_delta: Optional[datetime.timedelta] = None) -> str:
    if not SECRET_KEY:
        raise RuntimeError("JWT_SECRET environment variable is not set")
    to_encode = {"user_id": user_id, "role": role}
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenData(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> TokenData:
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing credentials")
    token = credentials.credentials
    return decode_token(token)
