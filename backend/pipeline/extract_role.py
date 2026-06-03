import sqlite3
import logging
import json
from pathlib import Path

from prompt_model import prompt_model

# ==========================================
# Config
# ==========================================

GREEN = "\033[92m"
RESET = "\033[0m"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

project_root = Path(__file__).resolve().parent.parent.parent
DB = project_root / "data" / "jobs_database.db"

MODEL_NAME = "gemini-3.1-flash-lite"


# ==========================================
# Database Setup
# ==========================================

def add_role_column(cursor):
    """Add role column if it does not exist."""
    try:
        cursor.execute("ALTER TABLE jobs ADD COLUMN role TEXT;")
        log.info("✅ Added role column to database")
    except sqlite3.OperationalError:
        # Column already exists
        log.info("ℹ️ Role column already exists, skipping")


def fetch_job_titles():
    """Fetch job titles without roles."""

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row  # So we can access row["title"]
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT title
        FROM jobs
        WHERE role IS NULL
           OR role = ''
    """)

    rows = cursor.fetchall()
    conn.close()

    return [row["title"] for row in rows]


def update_job_roles(role_mapping: dict):
    """Update role field in database."""

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    for job_title, role in role_mapping.items():
        cursor.execute("""
            UPDATE jobs
            SET role = ?
            WHERE title = ?
        """, (role, job_title))

    conn.commit()
    conn.close()


# ==========================================
# Prompt Building
# ==========================================

def build_batch_role_prompt(job_titles: list[str]) -> str:
    """Construct prompt for role classification."""
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


# ==========================================
# Utility
# ==========================================

def chunk_list(data: list, chunk_size: int = 20):
    """Split list into batches."""
    for i in range(0, len(data), chunk_size):
        yield i, data[i:i + chunk_size]


# ==========================================
# Main Classification Logic
# ==========================================

def classify_roles(job_titles: list[str]):
    """
    Send job titles to LLM in batches
    and store classified roles in DB.
    """
    if not job_titles:
        log.info("No job titles to process")
        return

    total_batches = (len(job_titles) + 19) // 20

    print(f"\n📊 Total job titles: {len(job_titles)}")
    print(f"📦 Total batches: {total_batches}")

    for batch_idx, batch in chunk_list(job_titles, 20):
        current_batch = (batch_idx // 20) + 1

        print(f"\n🚀 Processing batch {current_batch}/{total_batches}")
        print(f"   🧾 Batch size: {len(batch)}")

        prompt = build_batch_role_prompt(batch)

        print("   🤖 Calling LLM...")
        response = prompt_model(MODEL_NAME, prompt).strip()
        print(response)

        try:
            parsed = json.loads(response)

            if not isinstance(parsed, dict):
                raise ValueError(
                    "LLM response is not a dictionary"
                )

            print(f"   📌 Parsed {len(parsed)} roles")

            # Update DB
            update_job_roles(parsed)
            print("   💾 Saved to database")

        except json.JSONDecodeError:
            print("❌ JSON parsing failed")
            print(response)

        except Exception as e:
            print(f"❌ Error: {e}")


# ==========================================
# Pipeline Entry Point
# ==========================================

def run_role_extraction():
    """Pipeline entry point."""

    # Connect to DB to add role column
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    add_role_column(cursor)
    conn.commit()
    conn.close()

    job_titles = fetch_job_titles()

    if not job_titles:
        print("✅ No new jobs to classify")
        return

    classify_roles(job_titles)

    print(f"\n{GREEN}✅ Role extraction complete{RESET}")


if __name__ == "__main__":
    run_role_extraction()