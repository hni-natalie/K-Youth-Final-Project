import json
from collections import Counter
from backend.utils.error_handlers import InternalServerError
from backend.core.database.connection import get_db
from backend.pipeline.prompt_model import prompt_model

MODEL_NAME = "gemini-3.1-flash-lite"
BATCH_SIZE = 30


# =========================
# DB FETCH
# =========================
def fetch_tech_stack() -> list[str]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT tech_stack FROM jobs")
        rows = cursor.fetchall()

        if not rows:
            raise InternalServerError("No tech stack data found")

        data = [r["tech_stack"] for r in rows if r["tech_stack"]]
        print(f"📊 DB rows: {len(data)}")
        return data


# =========================
# SPLIT SKILLS
# =========================
def split_and_normalize_skills(rows: list[str]) -> list[str]:
    skills = []

    for i, row in enumerate(rows, start=1):
        parts = row.split(",")
        for p in parts:
            s = p.strip().lower()
            if s:
                skills.append(s)

        print(f"🔹 Row {i}: {len(parts)} skills")

    print(f"📊 Total raw skills: {len(skills)}")
    return skills


# =========================
# PROMPT
# =========================
def build_skill_filter_prompt(skills: list[str]) -> str:
    skills_text = "\n".join(f"- {s}" for s in skills)

    return f"""
You are a strict skill normalization system.

Return ONLY valid JSON ARRAY.

Each item must follow:
{{
  "skill": "original_skill",
  "normalized": "clean_skill_name or null"
}}

Rules:
- Remove non-tech skills
- Normalize synonyms (ai → artificial intelligence)
- No markdown
- No explanation

Skills:
{skills_text}
"""


# =========================
# LLM BATCH PROCESS
# =========================
def filter_skills_with_llm_batch(skills: list[str]) -> list[dict]:
    results = []

    for start in range(0, len(skills), BATCH_SIZE):
        batch = skills[start:start + BATCH_SIZE]

        print(f"\n🤖 Batch {start // BATCH_SIZE + 1}: {len(batch)} skills")

        prompt = build_skill_filter_prompt(batch)
        response = prompt_model(MODEL_NAME, prompt).strip()

        print(f"📥 Raw response preview:\n{response[:200]}...\n")

        try:
            parsed = json.loads(response)

            if not isinstance(parsed, list):
                raise ValueError("Expected list from LLM")

            results.extend(parsed)
            print(f"✅ Batch parsed: {len(parsed)} items")

        except Exception as e:
            print("❌ Failed batch response")
            print(response)
            raise InternalServerError(f"Batch parsing failed: {str(e)}")

    return results


# =========================
# MAIN PIPELINE
# =========================
def get_tech_stack_stats():
    try:
        # Step 1
        rows = fetch_tech_stack()

        # Step 2
        raw_skills = split_and_normalize_skills(rows)

        # Step 3
        unique_skills = list(set(raw_skills))
        print(f"\n📦 Unique skills: {len(unique_skills)}")

        # Step 4
        llm_results = filter_skills_with_llm_batch(unique_skills)

        # Step 5: build mapping
        skill_map = {}
        for item in llm_results:
            raw = item.get("skill")
            norm = item.get("normalized")

            if raw and norm:
                skill_map[raw] = norm

        print(f"\n🔗 Mapped skills: {len(skill_map)}")

        # Step 6: count
        counter = Counter()
        ignored = []

        for s in raw_skills:
            if s in skill_map:
                counter[skill_map[s]] += 1
            else:
                ignored.append(s)

        print(f"\n📊 Valid skills: {len(counter)}")
        print(f"⚠️ Ignored: {len(ignored)}")

        # Step 7: output
        result = dict(counter.most_common())

        print("\n🎯 FINAL RESULT")
        for k, v in result.items():
            print(f"{k}: {v}")

        return {
            "message": "Tech stack statistics retrieved successfully",
            "data": {
                "top_skills": result
            }
        }

    except Exception as e:
        print("💥 ERROR:", str(e))
        raise InternalServerError(str(e))
