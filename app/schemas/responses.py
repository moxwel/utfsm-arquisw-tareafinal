from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime
from .channels import ChannelType

class ChannelIDResponse(BaseModel):
    id: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "60f7c0c2b4d1c8b4f8e4d2a1",
            }
        }

class ChannelBasicInfoResponse(BaseModel):
    id: str
    name: str
    owner_id: str
    channel_type: ChannelType
    created_at: float
    user_count: int

    class Config:
        json_schema_extra = {
            "example": {
                "id": "60f7c0c2b4d1c8b4f8e4d2a1",
                "name": "general",
                "owner_id": "owner123",
                "channel_type": "public",
                "created_at": 1760833769.259725,
                "user_count": 5,
            }
        }