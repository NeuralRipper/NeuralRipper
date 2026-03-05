"""
Google OAuth login route
Frontend sends Google ID token -> we verify it -> find or create user -> return JWT

GET /auth/me -> validate JWT and return user info
"""

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.db import get_session
from dependencies.auth import get_current_user
from db.user import User
from schemas.auth import GoogleLoginRequest, TokenResponse, UserInfo
from settings import GOOGLE_CLIENT_ID, JWT_SECRET_KEY, JWT_ALGORITHM

router = APIRouter(prefix="/auth")


def create_jwt(user_id: int) -> str:
    """
    input:
        user_id: int user id from DB
    return:
        json web token: string

    jwt.encode() does all 3 steps internally:
    1. Header: {"alg": "HS256", "typ": "JWT"} -> base64url encode (algorithm to sign, type of token)
    2. Payload: {"sub": ..., "exp": ...} -> base64url encode (subject: user_id, expiration: time to expire token)
    3. Signature: HMAC-SHA256(base64url(header) + "." + base64url(payload), SECRET_KEY) -> base64url encode
    Final: header.payload.signature
    """
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=12),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


@router.post("/google", response_model=TokenResponse)
async def google_login(body: GoogleLoginRequest, session: AsyncSession = Depends(get_session)):
    """
    1. Verify Google ID token
    2. Extract user info (sub, email, name, picture)
    3. Find or create user in DB
    4. Return JWT + user info
    """
    try:
        id_info = id_token.verify_oauth2_token(
            body.token, google_requests.Request(), GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    google_id = id_info["sub"]
    email = id_info.get("email")
    name = id_info.get("name")
    avatar_url = id_info.get("picture")

    # find or create user
    result = await session.execute(select(User).where(User.google_id == google_id))
    db_user = result.scalar_one_or_none()

    if not db_user:
        db_user = User(google_id=google_id, email=email, name=name, avatar_url=avatar_url)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
    else:
        # update name/avatar in case they changed on Google's side
        db_user.name = name
        db_user.avatar_url = avatar_url
        await session.commit()
        await session.refresh(db_user)

    return TokenResponse(
        access_token=create_jwt(db_user.id),
        user=UserInfo.model_validate(db_user),
    )


@router.get("/me", response_model=UserInfo)
async def get_me(
    user_id: int = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Validate JWT and return current user info"""
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
