from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime
from .channels import ChannelType

class ChannelCreatePayload(BaseModel):
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

class ChannelUpdatePayload(BaseModel):
    name: Optional[str] = None
    owner_id: Optional[str] = None
    channel_type: Optional[ChannelType] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "random",
                "owner_id": "owner456",
                "channel_type": "private"
            }
        }

class ChannelUserPayload(BaseModel):
    channel_id: str
    user_id: str

    class Config:
        json_schema_extra = {
            "example": {
                "channel_id": "60f7c0c2b4d1c8b4f8e4d2a1",
                "user_id": "user123",
            }
        }

class ChannelThreadPayload(BaseModel):
    channel_id: str
    thread_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "channel_id": "60f7c0c2b4d1c8b4f8e4d2a1",
                "thread_id": "thread123",
            }
        }
