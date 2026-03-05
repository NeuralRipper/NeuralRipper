"""
JWT auth — one shared decode function, two entry points:

- get_current_user()  — HTTP routes, auto-extracts Bearer token via Depends()
- decode_jwt()        — WebSocket routes, call directly after reading first message

HTTP routes use HTTPBearer which reads the Authorization header automatically.
WebSocket has no HTTP headers after handshake, so the WS route reads the token
from the first JSON message and calls decode_jwt() directly.
"""

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from settings import JWT_SECRET_KEY, JWT_ALGORITHM

bearer_scheme = HTTPBearer()


def decode_jwt(token: str) -> int:
    """
    Decode JWT and return user_id (the "sub" claim).
    Raises jwt.ExpiredSignatureError or jwt.InvalidTokenError on failure.

    Used by:
    - get_current_user() for HTTP routes (called internally)
    - WebSocket routes (called directly after stripping "Bearer " prefix)
    """
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    return int(payload["sub"])


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> int:
    """
    HTTP route dependency, auto-extracts Bearer token from Authorization header.
    Usage: user_id: int = Depends(get_current_user)
    """
    try:
        return decode_jwt(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
