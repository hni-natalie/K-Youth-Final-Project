import json
import sqlite3

from backend.utils.error_handlers import InternalServerError
from backend.core.database.connection import get_db
from backend.pipeline.common.prompt_model import prompt_model

MODEL_NAME = "gemini-3.1-flash-lite"
BATCH_SIZE = 50


def ensure_normalized_column():
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(jobs)")
        columns = [row[1] for row in cursor.fetchall()]

        if "normalized_tech_stack" not in columns:
            cursor.execute("""
                ALTER TABLE jobs
                ADD COLUMN normalized_tech_stack TEXT
            """)
            conn.commit()
            print("🛠️ Added normalized_tech_stack column")


def clear_normalized_tech_stack():
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE jobs
            SET normalized_tech_stack = NULL
        """)
        conn.commit()

        print("🧹 Cleared normalized_tech_stack column")


def fetch_tech_stack_rows():
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT job_id, tech_stack
            FROM jobs
            WHERE normalized_tech_stack IS NULL
        """)

        rows = cursor.fetchall()

    if not rows:
        raise InternalServerError("No unprocessed tech stack data found")

    return rows


def split_and_normalize(rows):
    job_skills = {}
    all_skills = []

    for row in rows:
        job_id = row["job_id"]
        tech_stack = row["tech_stack"]

        if not tech_stack:
            continue

        skills = [s.strip().lower() for s in tech_stack.split(",") if s.strip()]

        job_skills[job_id] = skills
        all_skills.extend(skills)

    return job_skills, all_skills


def build_skill_filter_prompt(skills):
    skills_text = "\n".join(f"- {s}" for s in skills)

    return f"""
You are a strict technology skill normalization system.

Return ONLY a valid JSON ARRAY.

Each item must follow:
{{
  "skill": "original_skill",
  "normalized": "normalized_skill_or_null"
}}

Rules:
- Keep ONLY technical skills
- Remove soft skills, languages, vague terms, benefits, job traits
- Normalize synonyms:
  ai → artificial intelligence
  js → javascript
  ts → typescript
  nodejs → node.js
  reactjs → react
- Use lowercase
- Return null if not technical
- No markdown
- No explanation

Skills:
{skills_text}
"""


def normalize_skills_with_llm(skills):
    results = []

    for start in range(0, len(skills), BATCH_SIZE):
        batch = skills[start:start + BATCH_SIZE]

        print(f"🤖 Processing batch {start // BATCH_SIZE + 1} ({len(batch)} skills)")

        prompt = build_skill_filter_prompt(batch)
        response = prompt_model(MODEL_NAME, prompt).strip()

        try:
            parsed = json.loads(response)

            if not isinstance(parsed, list):
                raise ValueError("Expected JSON list")

            results.extend(parsed)

        except Exception as e:
            print("❌ Bad LLM response:\n", response)
            raise InternalServerError(f"LLM parsing failed: {e}")

    return results


def build_skill_map(llm_results):
    skill_map = {}

    for item in llm_results:
        raw = item.get("skill")
        norm = item.get("normalized")

        if raw and norm and isinstance(norm, str):
            skill_map[raw.strip().lower()] = norm.strip().lower()

    return skill_map


def update_normalized_skills(rows, job_skills, skill_map):
    with get_db() as conn:
        cursor = conn.cursor()

        for row in rows:
            job_id = row["job_id"]
            tech_stack = row["tech_stack"]

            if not tech_stack:
                cursor.execute("""
                    UPDATE jobs
                    SET normalized_tech_stack = NULL
                    WHERE job_id = ?
                """, (job_id,))
                continue

            skills = job_skills.get(job_id, [])
            normalized = []

            for s in skills:
                if s in skill_map:
                    normalized.append(skill_map[s])

            normalized = list(dict.fromkeys(normalized))

            normalized_text = ", ".join(normalized) if normalized else None

            cursor.execute("""
                UPDATE jobs
                SET normalized_tech_stack = ?
                WHERE job_id = ?
            """, (normalized_text, job_id))

        conn.commit()


def run_tech_stack_normalization_pipeline():
    try:
        print("\n🚀 Starting tech stack normalization pipeline...\n")

        ensure_normalized_column()

        rows = fetch_tech_stack_rows()
        print(f"📦 Rows fetched: {len(rows)}")

        job_skills, all_skills = split_and_normalize(rows)

        print(f"🔹 Total raw skills: {len(all_skills)}")
        print(f"🔹 Jobs processed: {len(job_skills)}")

        unique_skills = list(set(all_skills))
        print(f"📊 Unique skills: {len(unique_skills)}")

        llm_results = normalize_skills_with_llm(unique_skills)
        print(f"🤖 LLM results: {len(llm_results)}")

        skill_map = build_skill_map(llm_results)
        print(f"🔗 Skill map size: {len(skill_map)}")

        update_normalized_skills(rows, job_skills, skill_map)

        print("\n✅ DB updated successfully")

    except Exception as e:
        print("💥 Pipeline failed:", str(e))
        raise InternalServerError(str(e))


if __name__ == "__main__":
    run_tech_stack_normalization_pipeline()