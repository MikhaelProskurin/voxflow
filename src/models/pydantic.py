from enum import StrEnum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class TaskStatesEnum(StrEnum):
    open: str = "open"
    closed: str = "closed"
    deleted: str = "deleted"


class Task(BaseModel):
    telegram_user_id: int
    title: str
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool


class User(BaseModel):
    telegram_user_id: int
    telegram_username: str
    created_at: datetime
    updated_at: Optional[datetime]


class MessageTypesEnum(StrEnum):
    voice: str = "voice"
    text: str = "text"


class BaseUserMessage(BaseModel):
    telegram_user_id: int
    source: MessageTypesEnum
    content: str