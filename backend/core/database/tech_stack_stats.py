from collections import Counter
from backend.utils.error_handlers import InternalServerError
from backend.core.database.connection import get_db


# =========================
# FETCH NORMALIZED STACK
# =========================
def fetch_normalized_tech_stack(role: str | None = None) -> list[str]:
    with get_db() as conn:
        cursor = conn.cursor()

        if role:
            cursor.execute("""
                SELECT normalized_tech_stack
                FROM jobs
                WHERE role = ?
            """, (role,))
        else:
            cursor.execute("""
                SELECT normalized_tech_stack
                FROM jobs
                WHERE normalized_tech_stack IS NOT NULL
            """)

        rows = cursor.fetchall()

    if not rows:
        raise InternalServerError("No normalized tech stack data found")

    return [r["normalized_tech_stack"] for r in rows if r["normalized_tech_stack"]]


# =========================
# SPLIT STACK
# =========================
def split_normalized_stack(rows: list[str]) -> list[str]:
    skills = []

    for row in rows:
        for s in row.split(","):
            cleaned = s.strip().lower()
            if cleaned:
                skills.append(cleaned)

    return skills


# =========================
# MAIN STATS
# =========================
def get_tech_stack_stats(role: str | None = None):
    try:
        rows = fetch_normalized_tech_stack(role)

        raw_skills = split_normalized_stack(rows)

        counter = Counter(raw_skills)

        result = dict(counter.most_common())

        return {
            "message": "Tech stack statistics retrieved successfully",
            "data": {
                "role": role,
                "top_skills": result
            }
        }

    except Exception as e:
        raise InternalServerError(str(e))