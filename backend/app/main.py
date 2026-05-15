from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import hash_password
from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.models import Candidate, CandidateStatus, User, UserRole
from app.routers import auth, candidates
from app.seed_data import build_seed_candidates
from app.services.candidate_service import _skills_to_json


settings = get_settings()
app = FastAPI(title=settings.app_name)

@app.get("/")
def root():
    return {"message": "TechKraft API is running"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    seed_database()


def seed_database() -> None:
    db: Session = SessionLocal()
    try:
        admin = db.scalar(select(User).where(User.email == "admin@techkraft.dev"))
        if admin is None:
            admin = User(
                email="admin@techkraft.dev",
                hashed_password=hash_password("Password123!"),
                role=UserRole.admin,
            )
            db.add(admin)

        reviewer = db.scalar(select(User).where(User.email == "reviewer@techkraft.dev"))
        if reviewer is None:
            reviewer = User(
                email="reviewer@techkraft.dev",
                hashed_password=hash_password("Password123!"),
                role=UserRole.reviewer,
            )
            db.add(reviewer)

        for candidate_data in build_seed_candidates(total=60):
            existing_candidate = db.scalar(select(Candidate).where(Candidate.email == candidate_data["email"]))
            if existing_candidate is not None:
                continue
            db.add(
                Candidate(
                    name=candidate_data["name"],
                    email=candidate_data["email"],
                    role_applied=candidate_data["role_applied"],
                    status=candidate_data["status"],
                    skills=_skills_to_json(candidate_data["skills"]),
                    internal_notes=candidate_data["internal_notes"],
                )
            )
        db.commit()
    finally:
        db.close()


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(candidates.router)
