from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class PlayerCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "dragonslayer99",
                "email": "player@example.com",
                "password": "securepassword123",
            }
        }
    }


class PlayerOut(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    last_seen_at: datetime
    total_sessions: int

    model_config = {"from_attributes": True}


class PlayerUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
