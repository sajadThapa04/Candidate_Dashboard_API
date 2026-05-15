import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid.uuid4())


class CandidateStatus(str, enum.Enum):
    new = "new"
    reviewed = "reviewed"
    hired = "hired"
    rejected = "rejected"
    archived = "archived"


class UserRole(str, enum.Enum):
    reviewer = "reviewer"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.reviewer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    scores: Mapped[list["Score"]] = relationship(back_populates="reviewer")


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    role_applied: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    status: Mapped[CandidateStatus] = mapped_column(
        Enum(CandidateStatus), default=CandidateStatus.new, index=True, nullable=False
    )
    skills: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    internal_notes: Mapped[str] = mapped_column(Text, nullable=True)
    ai_summary: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    scores: Mapped[list["Score"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    reviewer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    note: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    candidate: Mapped[Candidate] = relationship(back_populates="scores")
    reviewer: Mapped[User] = relationship(back_populates="scores")


Index("ix_candidates_status_role", Candidate.status, Candidate.role_applied)
Index("ix_scores_candidate_reviewer", Score.candidate_id, Score.reviewer_id)
