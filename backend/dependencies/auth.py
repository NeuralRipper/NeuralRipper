"""
JWT auth dependency — use with Depends(get_current_user) on protected routes
Extracts user_id from Bearer token in Authorization header
"""

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from settings import JWT_SECRET_KEY, JWT_ALGORITHM

bearer_scheme = HTTPBearer()  # extracts Bearer <token> from Authorization header


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> int:
    try:
        # Exact same pattern like encode, with same key and algo to decode the jwt token and retrieve user info
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload["sub"]  # subject: user_id
    # HTTP 401, Unauthorized Error
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
