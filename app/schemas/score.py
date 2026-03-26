from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ScoreCreate(BaseModel):
    score: int
    gold_collected: int = 0
    enemies_smashed: int = 0
    wave_reached: int = 0

    model_config = {
        "json_schema_extra": {
            "example": {
                "score": 4200,
                "gold_collected": 310,
                "enemies_smashed": 47,
                "wave_reached": 12,
            }
        }
    }


class ScoreOut(BaseModel):
    id: int
    player_id: int
    score: int
    gold_collected: int
    enemies_smashed: int
    wave_reached: int
    created_at: datetime

    model_config = {"from_attributes": True}


class LeaderboardEntry(BaseModel):
    rank: int
    username: str
    score: int
    gold_collected: int
    enemies_smashed: int
    wave_reached: int
    created_at: datetime
