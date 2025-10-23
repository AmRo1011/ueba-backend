import os, time
from typing import Optional, Dict, Any
from jose import jwt, JWTError

ALGO = "HS256"
SECRET = os.getenv("JWT_SECRET", "change_me")

def create_token(sub: str, role: str = "user", expires_in: int = 3600) -> str:
    now = int(time.time())
    payload = {
        "sub": sub,
        "role": role,
        "iat": now,
        "exp": now + expires_in,
        "iss": "ueba.api"
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.decode(token, SECRET, algorithms=[ALGO], options={"verify_aud": False})
    except JWTError:
        return None
