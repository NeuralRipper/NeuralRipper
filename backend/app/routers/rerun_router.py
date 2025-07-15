from fastapi import APIRouter, status
from app.schemas.rerun_schema import RerunResponse
from app.handlers.rerun_handler import RerunHandler

router = APIRouter(prefix="/rerun", tags=["rerun"])

rerun_handler = RerunHandler()

@router.get("/display/{rid}", response_model=RerunResponse, status_code=status.HTTP_200_OK)
def display(rid: str):
    return rerun_handler.display(rid=rid)
