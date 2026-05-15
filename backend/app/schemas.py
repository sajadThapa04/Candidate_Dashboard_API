from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import CandidateStatus, UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    role: UserRole
    created_at: datetime


class CandidateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    role_applied: str = Field(min_length=1, max_length=120)
    status: CandidateStatus = CandidateStatus.new
    skills: list[str] = Field(default_factory=list)
    internal_notes: str | None = None


class CandidateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    role_applied: str | None = Field(default=None, min_length=1, max_length=120)
    status: CandidateStatus | None = None
    skills: list[str] | None = None
    internal_notes: str | None = None


class ScoreCreate(BaseModel):
    category: str = Field(min_length=1, max_length=80)
    score: Annotated[int, Field(ge=1, le=5)]
    note: str | None = Field(default=None, max_length=1000)


class ScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    candidate_id: str
    category: str
    score: int
    reviewer_id: str
    note: str | None
    created_at: datetime


class CandidateListItem(BaseModel):
    id: str
    name: str
    email: EmailStr
    role_applied: str
    status: CandidateStatus
    skills: list[str]
    created_at: datetime


class CandidateDetail(CandidateListItem):
    scores: list[ScoreRead]
    ai_summary: str | None = None
    internal_notes: str | None = None


class CandidatePage(BaseModel):
    items: list[CandidateListItem]
    total: int
    offset: int
    limit: int


class SummaryRead(BaseModel):
    candidate_id: str
    summary: str
