from pydantic import BaseModel


class RerunResponse(BaseModel):
    msg: str