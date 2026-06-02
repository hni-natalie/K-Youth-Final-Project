import sqlite3
import logging
import time
from pathlib import Path 
from prompt_model import prompt_model

GREEN = "\033[92m"
RESET = "\033[0m"

project_root = Path(__file__).resolve().parent.parent.parent
DB = project_root / "data" / "jobs_database.db"

MODEL = "gemini-3.1-flash-lite"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# Batch Config
BATCH_SIZE = 20
RETRY_DELAY = 2
MAX_RETRIES = 3

BATCH_PROMPT = """
You are a machine parser.

You MUST follow these rules exactly:

- Output ONLY raw results
- NO titles
- NO introduction
- NO explanation
- NO headings
- NO markdown
- NO extra text before or after

OUTPUT FORMAT (STRICT):
Each line must be exactly:
<JobID>: <tech1>, <tech2>, <tech3>

HARD RULES:
- Output must start immediately with a JobID
- First character of output must be a digit
- Do NOT output any sentence or label
- Do NOT output "Here is..."
- Do NOT output any preamble
- Do NOT output fewer or more lines than input
- If no technical stack is found, output:
  <JobID>: none

If you break format, output is invalid.

INPUT:
"""

def add_tech_stack_column(cursor):
    try:
        cursor.execute("ALTER TABLE jobs ADD COLUMN tech_stack TEXT;")
        log.info("✅ Added tech_stack column to database")
    except sqlite3.OperationalError:
        # Column already exists
        pass


def get_batch(cursor):
    cursor.execute("""
        SELECT job_id, job_description
        FROM jobs
        WHERE tech_stack IS NULL OR tech_stack = ''
        LIMIT ?
    """, (BATCH_SIZE,))
    return cursor.fetchall()


def build_prompt(batch):
    prompt = BATCH_PROMPT
    for job_id, description in batch:
        prompt += f"\nJob ID: {job_id}\nDescription:\n{description}"
    return prompt


def parse_response(response, batch_size):
    lines = [
        line.strip()
        for line in response.strip().split("\n")
        if line.strip()
    ]

    valid_lines = []
    for line in lines:
        if ":" in line:
            job_id, tech = line.split(":", 1)
            if job_id.strip().isdigit():
                valid_lines.append(line)

    if len(valid_lines) != batch_size:
        raise ValueError(f"Mismatch: expected {batch_size}, got {len(valid_lines)}")

    return valid_lines


def update_database(cursor, responses):
    for res in responses:
        if ":" not in res:
            continue

        job_id, tech_stack = res.split(":", 1)
        job_id = job_id.strip()
        tech_stack = tech_stack.strip()

        cursor.execute("""
            UPDATE jobs
            SET tech_stack = ?
            WHERE job_id = ?
        """, (tech_stack, job_id))

        log.info(f"Analyzed Job {GREEN}{job_id}{RESET}: {tech_stack}")  


def tag_data(db_url: str):
    conn = None

    try:
        conn = sqlite3.connect(db_url)
        cursor = conn.cursor()

        # Ensure column exists
        add_tech_stack_column(cursor)

        # Optional: clear previous tech stack
        cursor.execute("UPDATE jobs SET tech_stack = NULL")
        conn.commit()

        batch_num = 0

        while True:
            batch = get_batch(cursor)
            if not batch:
                log.info("\n[INFO] All jobs processed ✅")
                break

            batch_num += 1
            attempt = 0
            success = False
            log.info(f"\n=== Processing Batch {batch_num} ===")

            while attempt < MAX_RETRIES:
                attempt += 1
                try:
                    prompt = build_prompt(batch)
                    response = prompt_model(MODEL, prompt)       
                    responses = parse_response(response, len(batch))
                    update_database(cursor, responses)
                    conn.commit()
                    success = True
                    break 

                except Exception as e:
                    log.error(f"[Batch {batch_num}] Attempt {attempt} failed: {e}")
                    time.sleep(RETRY_DELAY)

            if not success:
                log.error(f"[Batch {batch_num}] Failed after {MAX_RETRIES} attempts")
                break

    except Exception as e:
        log.error(f"Fatal error: {e}")

    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    tag_data(DB)