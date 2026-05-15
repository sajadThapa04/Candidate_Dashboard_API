from app.models import CandidateStatus


FIRST_NAMES = [
    "Maya",
    "Aarav",
    "Nima",
    "Asha",
    "Kiran",
    "Sofia",
    "Liam",
    "Priya",
    "Noah",
    "Anika",
    "Ethan",
    "Sara",
]

LAST_NAMES = [
    "Sharma",
    "Rai",
    "Lama",
    "Gurung",
    "Thapa",
    "Patel",
    "Chen",
    "Garcia",
    "Kim",
    "Adhikari",
]

ROLES = [
    "Full Stack Engineer",
    "Backend Engineer",
    "Frontend Engineer",
    "DevOps Engineer",
    "Data Engineer",
    "QA Automation Engineer",
]

SKILL_GROUPS = [
    ["Python", "FastAPI", "React", "SQL"],
    ["Node.js", "Express", "PostgreSQL", "Docker"],
    ["React", "TypeScript", "Vite", "CSS"],
    ["AWS", "Terraform", "Docker", "CI/CD"],
    ["Python", "Pandas", "Airflow", "DynamoDB"],
    ["Playwright", "Pytest", "Selenium", "API Testing"],
    ["Java", "Spring Boot", "MySQL", "Kafka"],
    ["Go", "Kubernetes", "Redis", "PostgreSQL"],
]

STATUSES = [
    CandidateStatus.new,
    CandidateStatus.reviewed,
    CandidateStatus.hired,
    CandidateStatus.rejected,
]


def build_seed_candidates(total: int = 60) -> list[dict]:
    candidates = []
    for index in range(total):
        first_name = FIRST_NAMES[index % len(FIRST_NAMES)]
        last_name = LAST_NAMES[(index * 3) % len(LAST_NAMES)]
        role = ROLES[index % len(ROLES)]
        skills = SKILL_GROUPS[index % len(SKILL_GROUPS)]
        status = STATUSES[index % len(STATUSES)]
        sequence = index + 1

        candidates.append(
            {
                "name": f"{first_name} {last_name}",
                "email": f"{first_name.lower()}.{last_name.lower()}.{sequence}@example.com",
                "role_applied": role,
                "status": status,
                "skills": skills,
                "internal_notes": (
                    f"Seeded candidate {sequence}. Review emphasis: "
                    f"{skills[0]} and {skills[1]} for {role}."
                ),
            }
        )
    return candidates
