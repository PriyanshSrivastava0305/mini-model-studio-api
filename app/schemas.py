from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional
from uuid import UUID

# Model profile schemas


class ModelProfileCreate(BaseModel):
    name: str = Field(..., example="Helpful Assistant")
    provider: str = Field(..., example="openai")
    base_model: str = Field(..., example="gpt-4o-mini")
    system_prompt: str = Field(..., example="You are a helpful assistant...")


class ModelProfileUpdate(BaseModel):
    name: Optional[str]
    provider: Optional[str]
    base_model: Optional[str]
    system_prompt: Optional[str]


class ModelProfileOut(BaseModel):
    id: UUID
    name: str
    provider: str
    base_model: str
    system_prompt: str
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

# Chat and message schemas


class ChatCreate(BaseModel):
    title: Optional[str]
    model_profile_id: Optional[UUID]


class ChatOut(BaseModel):
    id: UUID
    title: Optional[str]
    model_profile_id: Optional[UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class MessageIn(BaseModel):
    content: str
    model_profile_id: Optional[UUID] = None  # optional override


class MessageOut(BaseModel):
    id: UUID
    chat_id: UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
