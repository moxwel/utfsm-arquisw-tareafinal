from typing import Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

class ChannelType(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"

class ChannelMember(BaseModel):
    id: str
    joined_at: float

class Channel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    owner_id: str
    users: list[ChannelMember]
    is_active: bool = True
    channel_type: ChannelType = ChannelType.PUBLIC
    created_at: float
    updated_at: float
    deleted_at: Optional[float] = None

    class Config:
        validate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        json_schema_extra = {
            "example": {
            "_id": "68f430e95055d3561d1d3167",
            "name": "general",
            "owner_id": "owner123",
            "users": [
                {"id": "user1", "joined_at": 1760833769.259725},
                {"id": "user2", "joined_at": 1760833769.259725},
                {"id": "owner123", "joined_at": 1760833769.259725}
            ],
            "is_active": True,
            "channel_type": "public",
            "created_at": 1760833769.259725,
            "updated_at": 1760833769.259725,
            "deleted_at": None
            }
        }
