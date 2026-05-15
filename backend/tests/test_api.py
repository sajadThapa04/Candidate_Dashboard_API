from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from app.auth import hash_password
from app.database import Base, get_db
from app.main import app
from app.models import Candidate, CandidateStatus, User, UserRole
from app.services.candidate_service import _skills_to_json


SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        admin = User(
            email="admin@test.dev",
            hashed_password=hash_password("Password123!"),
            role=UserRole.admin,
        )
        reviewer_one = User(
            email="reviewer1@test.dev",
            hashed_password=hash_password("Password123!"),
            role=UserRole.reviewer,
        )
        reviewer_two = User(
            email="reviewer2@test.dev",
            hashed_password=hash_password("Password123!"),
            role=UserRole.reviewer,
        )
        candidate = Candidate(
            name="Asha Rai",
            email="asha@example.com",
            role_applied="Backend Engineer",
            status=CandidateStatus.new,
            skills=_skills_to_json(["Python", "FastAPI"]),
            internal_notes="Admin-only context",
        )
        db.add_all([admin, reviewer_one, reviewer_two, candidate])
        db.commit()
        return {
            "admin_id": admin.id,
            "reviewer_one_id": reviewer_one.id,
            "reviewer_two_id": reviewer_two.id,
            "candidate_id": candidate.id,
        }
    finally:
        db.close()


def auth_headers(client: TestClient, email: str) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": email, "password": "Password123!"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_create_candidate():
    reset_database()
    client = TestClient(app)
    headers = auth_headers(client, "admin@test.dev")

    response = client.post(
        "/candidates",
        headers=headers,
        json={
            "name": "Nima Lama",
            "email": "nima@example.com",
            "role_applied": "Frontend Engineer",
            "skills": ["React", "TypeScript"],
            "internal_notes": "Portfolio looks polished.",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "nima@example.com"


def test_registration_always_creates_reviewer_role():
    reset_database()
    client = TestClient(app)

    response = client.post(
        "/auth/register",
        json={"email": "new-user@test.dev", "password": "Password123!", "role": "admin"},
    )

    assert response.status_code == 201
    assert response.json()["role"] == "reviewer"


def test_reviewer_only_sees_own_scores_and_no_internal_notes():
    ids = reset_database()
    client = TestClient(app)

    reviewer_one_headers = auth_headers(client, "reviewer1@test.dev")
    reviewer_two_headers = auth_headers(client, "reviewer2@test.dev")

    first_score = client.post(
        f"/candidates/{ids['candidate_id']}/scores",
        headers=reviewer_one_headers,
        json={"category": "Technical", "score": 5, "note": "Strong API instincts."},
    )
    second_score = client.post(
        f"/candidates/{ids['candidate_id']}/scores",
        headers=reviewer_two_headers,
        json={"category": "Communication", "score": 3, "note": "Needs clearer tradeoff notes."},
    )

    assert first_score.status_code == 201
    assert second_score.status_code == 201

    response = client.get(f"/candidates/{ids['candidate_id']}", headers=reviewer_one_headers)

    assert response.status_code == 200
    body = response.json()
    assert "internal_notes" not in body
    assert len(body["scores"]) == 1
    assert body["scores"][0]["reviewer_id"] == ids["reviewer_one_id"]
