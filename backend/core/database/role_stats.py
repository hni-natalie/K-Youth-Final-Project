import json
from collections import Counter
from backend.utils.error_handlers import InternalServerError
from backend.core.database.connection import get_db
from backend.pipeline.prompt_model import prompt_model

MODEL_NAME = "gemini-3.1-flash-lite"


def fetch_job_titles() -> list[str]:
    """Fetch distinct job titles from DB."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT title FROM jobs")
        rows = cursor.fetchall()

        if not rows:
            raise InternalServerError("No jobs found in database")

        return [row["title"] for row in rows]


def chunk_list(data: list, chunk_size: int = 20):
    """Split list into batches."""
    for i in range(0, len(data), chunk_size):
        yield i, data[i:i + chunk_size]


def build_batch_role_prompt(job_titles: list[str]) -> str:
    """Construct the LLM prompt for classifying a batch of job titles."""
    titles_text = "\n".join(f"- {t}" for t in job_titles)

    return f"""
You are a job title classification system for tech-related jobs.

Task:
1. Classify each job title into ONE standardized tech role category.
2. Merge semantically similar roles into a canonical name.
3. Ignore seniority, internship labels, departments, codes, and brackets.
4. Avoid duplicate naming styles.

Rules:
- Return ONLY JSON
- No markdown
- No explanation
- Use concise role names

Return format:
{{
  "Job Title": "Role"
}}

Job Titles:
{titles_text}
"""


def classify_roles(job_titles: list[str]) -> list[dict]:
    """
    Send job titles to LLM in batches and collect all responses.

    Returns:
        List of dictionaries, one per batch:
        [
            {"Senior Software Engineer": "Software Engineering", ...},
            {"Data Scientist": "Data Science", ...}
        ]
    """
    total_batches = (len(job_titles) + 19) // 20

    print(f"📊 Total job titles: {len(job_titles)}")
    print(f"📦 Total batches: {total_batches}")

    all_llm_responses = []

    for batch_idx, batch in chunk_list(job_titles, 20):
        current_batch = (batch_idx // 20) + 1

        print(f"\n🚀 Processing batch {current_batch}/{total_batches}")
        print(f"   🧾 Batch size: {len(batch)}")

        prompt = build_batch_role_prompt(batch)

        print("   🤖 Calling LLM...")
        response = prompt_model(MODEL_NAME, prompt).strip()

        try:
            parsed = json.loads(response)

            if not isinstance(parsed, dict):
                raise ValueError("LLM response is not a dictionary")

            print(f"   📌 Parsed {len(parsed)} items")
            all_llm_responses.append(parsed)

        except json.JSONDecodeError:
            print("❌ JSON parsing failed")
            print(response)
            raise InternalServerError("Invalid LLM JSON response")

    return all_llm_responses


def get_roles():
    """Return distinct roles from job titles."""
    try:
        job_titles = fetch_job_titles()

        llm_responses = classify_roles(job_titles)

        roles_set = set()
        for response in llm_responses:
            for role in response.values():
                roles_set.add(role)

        roles_list = sorted(roles_set)

        print("\n🎯 FINAL RESULT")
        print(f"   Roles extracted: {roles_list}")

        return {
            "message": "Roles retrieved successfully",
            "data": {
                "roles": roles_list
            }
        }

    except Exception as e:
        print("💥 ERROR OCCURRED:", str(e))
        raise InternalServerError(f"Failed to fetch roles: {str(e)}")


def get_roles_with_stats():
    """Return roles with number of appearances."""
    try:
        job_titles = fetch_job_titles()

        llm_responses = classify_roles(job_titles)

        role_counter = Counter()

        for response in llm_responses:
            for role in response.values():
                role_counter[role] += 1

        # Sort by highest count first
        stats_list = sorted(
            [
                {"role": role, "count": count}
                for role, count in role_counter.items()
            ],
            key=lambda x: x["count"],
            reverse=True
        )

        print("\n🎯 Role Stats:")
        for stat in stats_list:
            print(f"   {stat['role']}: {stat['count']}")

        return {
            "message": "Role statistics retrieved successfully",
            "data": {
                "roles": stats_list
            }
        }

    except Exception as e:
        print("💥 ERROR OCCURRED:", str(e))
        raise InternalServerError(
            f"Failed to fetch role stats: {str(e)}"
        )