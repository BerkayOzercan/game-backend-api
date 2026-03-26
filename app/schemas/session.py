from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SessionCreate(BaseModel):
    pass


class SessionEnd(BaseModel):
    score_id: int

    model_config = {
        "json_schema_extra": {
            "example": {"score_id": 42}
        }
    }


class SessionOut(BaseModel):
    id: int
    player_id: int
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]
    status: str
    final_score_id: Optional[int]

    model_config = {"from_attributes": True}
