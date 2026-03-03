import os
import json
import time
from typing import Optional, Dict, Any
from jose import jwt, JWTError
import urllib.request
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

# These should be in .env
CLERK_API_URL = os.getenv("CLERK_API_URL", "https://api.clerk.com/v1")
CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL") # Example: https://clerk.yourdomain.com/.well-known/jwks.json
CLERK_FRONTEND_API = os.getenv("VITE_CLERK_PUBLISHABLE_KEY", "").split("_")[1] if "_" in os.getenv("VITE_CLERK_PUBLISHABLE_KEY", "") else ""

_jwks_cache: Dict[str, Any] = {}
_last_fetch = 0
CACHE_TTL = 3600 # 1 hour

def fetch_jwks(url: str) -> Dict[str, Any]:
    global _jwks_cache, _last_fetch
    now = time.time()
    if url in _jwks_cache and (now - _last_fetch) < CACHE_TTL:
        return _jwks_cache[url]
    
    try:
        with urllib.request.urlopen(url) as response:
            jwks = json.loads(response.read().decode())
            _jwks_cache[url] = jwks
            _last_fetch = now
            return jwks
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch JWKS from Clerk: {str(e)}")

async def get_clerk_user(auth: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    token = auth.credentials
    
    if not CLERK_JWKS_URL:
        # If JWKS URL is not provided, we try to derive it or expect it in ENV
        raise HTTPException(status_code=500, detail="CLERK_JWKS_URL not configured")

    jwks = fetch_jwks(CLERK_JWKS_URL)
    
    try:
        # Get the unverified header to find the key ID (kid)
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        
        # Find the correct key in JWKS
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail="Invalid token header (kid not found)")
            
        # Verify the JWT
        # Note: Clerk tokens are RS256
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            options={"verify_aud": False} # Adjust as needed
        )
        
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Could not validate Clerk token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authentication")
