import asyncio
import json

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Candidate, CandidateStatus, Score, User, UserRole
from app.schemas import CandidateCreate, CandidateUpdate, ScoreCreate


def _skills_to_json(skills: list[str]) -> str:
    clean_skills = [skill.strip() for skill in skills if skill.strip()]
    return json.dumps(clean_skills)


def skills_from_json(raw_skills: str | None) -> list[str]:
    if not raw_skills:
        return []
    try:
        parsed = json.loads(raw_skills)
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def serialize_candidate_list_item(candidate: Candidate) -> dict:
    return {
        "id": candidate.id,
        "name": candidate.name,
        "email": candidate.email,
        "role_applied": candidate.role_applied,
        "status": candidate.status,
        "skills": skills_from_json(candidate.skills),
        "created_at": candidate.created_at,
    }


def serialize_candidate_detail(candidate: Candidate, current_user: User) -> dict:
    visible_scores = candidate.scores
    if current_user.role == UserRole.reviewer:
        visible_scores = [score for score in candidate.scores if score.reviewer_id == current_user.id]

    data = serialize_candidate_list_item(candidate)
    data["scores"] = visible_scores
    data["ai_summary"] = candidate.ai_summary
    if current_user.role == UserRole.admin:
        data["internal_notes"] = candidate.internal_notes
    return data


def list_candidates(
    db: Session,
    *,
    status_filter: CandidateStatus | None,
    role_applied: str | None,
    skill: str | None,
    keyword: str | None,
    offset: int,
    limit: int,
) -> tuple[list[Candidate], int]:
    conditions = [Candidate.status != CandidateStatus.archived]

    if status_filter:
        conditions.append(Candidate.status == status_filter)
    if role_applied:
        conditions.append(Candidate.role_applied.ilike(f"%{role_applied}%"))
    if skill:
        conditions.append(Candidate.skills.ilike(f"%{skill}%"))
    if keyword:
        search_term = f"%{keyword}%"
        conditions.append(
            or_(
                Candidate.name.ilike(search_term),
                Candidate.email.ilike(search_term),
                Candidate.role_applied.ilike(search_term),
            )
        )

    total = db.scalar(select(func.count()).select_from(Candidate).where(*conditions)) or 0
    candidates = db.scalars(
        select(Candidate)
        .where(*conditions)
        .order_by(Candidate.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return list(candidates), total


def get_candidate_or_404(db: Session, candidate_id: str) -> Candidate:
    candidate = db.scalar(
        select(Candidate).options(selectinload(Candidate.scores)).where(Candidate.id == candidate_id)
    )
    if candidate is None or candidate.status == CandidateStatus.archived:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    return candidate


def create_candidate(db: Session, payload: CandidateCreate) -> Candidate:
    candidate = Candidate(
        name=payload.name,
        email=str(payload.email),
        role_applied=payload.role_applied,
        status=payload.status,
        skills=_skills_to_json(payload.skills),
        internal_notes=payload.internal_notes,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return candidate


def update_candidate(db: Session, candidate: Candidate, payload: CandidateUpdate) -> Candidate:
    changes = payload.model_dump(exclude_unset=True)
    if "skills" in changes and changes["skills"] is not None:
        candidate.skills = _skills_to_json(changes.pop("skills"))
    for field, value in changes.items():
        setattr(candidate, field, value)
    db.commit()
    db.refresh(candidate)
    return candidate


def add_score(db: Session, candidate: Candidate, reviewer: User, payload: ScoreCreate) -> Score:
    score = Score(
        candidate_id=candidate.id,
        category=payload.category,
        score=payload.score,
        reviewer_id=reviewer.id,
        note=payload.note,
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    return score


async def generate_mock_summary(db: Session, candidate: Candidate) -> str:
    await asyncio.sleep(2)
    scores = list(candidate.scores)
    if scores:
        average = round(sum(item.score for item in scores) / len(scores), 1)
        score_text = f"Average reviewer score is {average}/5 across {len(scores)} submitted score(s)."
    else:
        score_text = "No reviewer scores have been submitted yet."

    skills = ", ".join(skills_from_json(candidate.skills)) or "no listed skills"
    summary = (
        f"{candidate.name} is applying for {candidate.role_applied} with skills in {skills}. "
        f"{score_text} Current pipeline status is {candidate.status.value}."
    )
    candidate.ai_summary = summary
    db.commit()
    db.refresh(candidate)
    return summary
