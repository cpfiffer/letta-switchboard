from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class RecurringScheduleCreate(BaseModel):
    agent_id: str
    cron: str
    message: str
    role: str = "user"
    timezone: str = "UTC"


class RecurringSchedule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    api_key: str
    cron: str
    message: str
    role: str = "user"
    timezone: str = "UTC"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None


class OneTimeScheduleCreate(BaseModel):
    agent_id: str
    execute_at: str
    message: str
    role: str = "user"


class OneTimeSchedule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    api_key: str
    execute_at: str
    message: str
    role: str = "user"
    created_at: datetime = Field(default_factory=datetime.utcnow)
