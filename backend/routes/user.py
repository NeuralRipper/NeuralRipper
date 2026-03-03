from fastapi import APIRouter, Depends
from db.session import get_session
from schemas.user import UserResponse, UserCreate
from sqlalchemy.ext.asyncio import AsyncSession
from db.user import User

router = APIRouter(prefix="/users")


@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, session: AsyncSession = Depends(get_session)):
    """
    user: the RequestBody defined as UserCreate
    session: injected via Depends(get_session)
    """
    db_user = User(**db_user.model_dump())      # pydantic -> ORM  unpack and map to ORM instance
    session.add(db_user)                        # stage
    await session.commit()                      # write to Db
    await session.refresh(db_user)              # reload to get auto-gen id, created_at
    return db_user                              # FastAPI converts ORM -> UserResponse via from_attributes
