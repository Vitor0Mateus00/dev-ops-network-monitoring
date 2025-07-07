from pydantic import BaseModel


class TargetModel(BaseModel):
    target: str
