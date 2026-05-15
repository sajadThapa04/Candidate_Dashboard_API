import asyncio
import json

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_admin
from app.database import get_db
from app.models import CandidateStatus, User
from app.schemas import (
    CandidateCreate,
    CandidateDetail,
    CandidateListItem,
    CandidatePage,
    CandidateUpdate,
    ScoreCreate,
    ScoreRead,
    SummaryRead,
)
from app.services import candidate_service


router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.get("", response_model=CandidatePage)
def list_candidates(
    status_filter: CandidateStatus | None = Query(default=None, alias="status"),
    role_applied: str | None = None,
    skill: str | None = None,
    keyword: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidates, total = candidate_service.list_candidates(
        db,
        status_filter=status_filter,
        role_applied=role_applied,
        skill=skill,
        keyword=keyword,
        offset=offset,
        limit=limit,
    )
    return {
        "items": [candidate_service.serialize_candidate_list_item(candidate) for candidate in candidates],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.post("", response_model=CandidateListItem, status_code=status.HTTP_201_CREATED)
def create_candidate(
    payload: CandidateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    candidate = candidate_service.create_candidate(db, payload)
    return candidate_service.serialize_candidate_list_item(candidate)


@router.get("/{candidate_id}", response_model=CandidateDetail, response_model_exclude_none=True)
def get_candidate(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidate = candidate_service.get_candidate_or_404(db, candidate_id)
    return candidate_service.serialize_candidate_detail(candidate, current_user)


@router.patch("/{candidate_id}", response_model=CandidateDetail, response_model_exclude_none=True)
def update_candidate(
    candidate_id: str,
    payload: CandidateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    candidate = candidate_service.get_candidate_or_404(db, candidate_id)
    candidate = candidate_service.update_candidate(db, candidate, payload)
    return candidate_service.serialize_candidate_detail(candidate, current_user)


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_candidate(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    candidate = candidate_service.get_candidate_or_404(db, candidate_id)
    candidate.status = CandidateStatus.archived
    db.commit()


@router.post("/{candidate_id}/scores", response_model=ScoreRead, status_code=status.HTTP_201_CREATED)
def submit_score(
    candidate_id: str,
    payload: ScoreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidate = candidate_service.get_candidate_or_404(db, candidate_id)
    return candidate_service.add_score(db, candidate, current_user, payload)


@router.post("/{candidate_id}/summary", response_model=SummaryRead)
async def generate_summary(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidate = candidate_service.get_candidate_or_404(db, candidate_id)
    summary = await candidate_service.generate_mock_summary(db, candidate)
    return {"candidate_id": candidate.id, "summary": summary}


@router.get("/{candidate_id}/stream")
async def stream_score_updates(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidate_service.get_candidate_or_404(db, candidate_id)

    async def event_generator():
        for _ in range(15):
            candidate = candidate_service.get_candidate_or_404(db, candidate_id)
            data = candidate_service.serialize_candidate_detail(candidate, current_user)
            payload = json.dumps(
                {
                    "candidate_id": candidate_id,
                    "scores": [
                        {
                            "id": score.id,
                            "category": score.category,
                            "score": score.score,
                            "reviewer_id": score.reviewer_id,
                            "note": score.note,
                            "created_at": score.created_at.isoformat(),
                        }
                        for score in data["scores"]
                    ],
                }
            )
            yield f"event: score_update\ndata: {payload}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
