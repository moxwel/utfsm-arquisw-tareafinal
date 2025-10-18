from typing import Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

class ChannelType(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"

class Channel(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    name: str
    owner_id: str
    users: list[str]
    is_active: bool = True
    channel_type: ChannelType = ChannelType.PUBLIC
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    deleted_at: Optional[datetime] = None

    class Config:
        validate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        json_schema_extra = {
            "example": {
                "name": "general",
                "owner_id": "owner123",
                "users": ["user1", "user2"],
                "is_active": True,
                "channel_type": "public",
            }
        }

class ChannelCreate(BaseModel):
    name: str
    owner_id: str
    users: list[str]  # List of user IDs
    channel_type: ChannelType = ChannelType.PUBLIC

    class Config:
        json_schema_extra = {
            "example": {
                "name": "general",
                "owner_id": "owner123",
                "users": ["user1", "user2"],
                "channel_type": "public",
            }
        }
    
class ChannelUpdate(BaseModel):
    name: Optional[str] = None
    owner_id: Optional[str] = None
    users: Optional[list[str]] = None
    is_active: Optional[bool] = None
    channel_type: Optional[ChannelType] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "random",
                "owner_id": "owner456",
                "users": ["user1", "user3"],
                "is_active": False,
                "channel_type": "private",
            }
        }

class ChannelDelete(BaseModel):
    id: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "60f7c0c2b4d1c8b4f8e4d2a1",
            }
        }

class AddDeleteUserChannel(BaseModel):
    channel_id: str
    user_id: str

    class Config:
        json_schema_extra = {
            "example": {
                "channel_id": "60f7c0c2b4d1c8b4f8e4d2a1",
                "user_id": "user123",
            }
        }