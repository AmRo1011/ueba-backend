import requests, json
from jose import jwt
from fastapi import HTTPException, Depends, Request
from datetime import datetime

JWKS_CACHE = None
JWKS_URL = None
ISS = None
AUD = None

def init_jwks():
    global JWKS_CACHE, JWKS_URL, ISS, AUD
    from app.core.config import settings
    JWKS_URL = settings.SUPABASE_JWKS_URL
    ISS = settings.SUPABASE_ISS
    AUD = settings.SUPABASE_AUDIENCE
    if not JWKS_URL:
        raise RuntimeError("SUPABASE_JWKS_URL not set")
    if JWKS_CACHE is None:
        res = requests.get(JWKS_URL)
        res.raise_for_status()
        JWKS_CACHE = res.json()

def verify_jwt(token: str):
    if JWKS_CACHE is None:
        init_jwks()
    try:
        header = jwt.get_unverified_header(token)
        key = next((k for k in JWKS_CACHE["keys"] if k["kid"] == header["kid"]), None)
        if not key:
            raise HTTPException(status_code=401, detail="Invalid key id")
        return jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=AUD,
            issuer=ISS,
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"JWT invalid: {e}")

def get_current_user(request: Request):
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = auth.split(" ")[1]
    claims = verify_jwt(token)
    return {
        "sub": claims.get("sub"),
        "email": claims.get("email"),
        "role": claims.get("role") or claims.get("app_metadata", {}).get("role", "user"),
        "exp": datetime.utcfromtimestamp(claims.get("exp")),
    }
