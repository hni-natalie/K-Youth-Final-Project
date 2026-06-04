from pathlib import Path
import sqlite3
import glob
import json
import time

from backend.pipeline.common.extract_role import run_role_extraction
from backend.pipeline.common.extract_tech_stack import tag_data

# =========================
# PATHS
# =========================
project_root = Path(__file__).resolve().parent.parent.parent.parent

NEW_JSON_DIR = project_root / "data" / "job_data" / "new"
DB_PATH = project_root / "data" / "jobs_database.db"


# =========================
# CONNECT DB
# =========================
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn, conn.cursor()


# =========================
# GET EXISTING IDS
# =========================
def get_existing_job_ids(cursor):
    cursor.execute("SELECT job_id FROM jobs")
    return {str(r[0]) for r in cursor.fetchall()}


# =========================
# INSERT JOB
# =========================
def insert_job(cursor, job):
    cursor.execute("""
        INSERT INTO jobs (
            job_id,
            title,
            job_url,
            company,
            location,
            salary,
            posted_date,
            actual_posted_date,
            job_description
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job["job_id"],
        job["title"],
        job["job_url"],
        job["company"],
        job["location"],
        job["salary"],
        job["posted_date"],
        job["actual_posted_date"],
        job["job_description"]
    ))


# =========================
# MAIN PROCESS
# =========================
def main():
    start = time.time()

    conn, cursor = get_connection()

    existing_ids = get_existing_job_ids(cursor)
    print(f"📂 Loaded {len(existing_ids)} existing jobs from DB")

    files = glob.glob(str(NEW_JSON_DIR / "*.json"))

    inserted = 0
    skipped = 0
    failed = 0

    for file in files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                job = json.load(f)

            job_id = str(job["job_id"])

            # skip duplicates
            if job_id in existing_ids:
                skipped += 1
                continue

            insert_job(cursor, job)
            existing_ids.add(job_id)

            print(f"💾 INSERTED: {job['title']}")
            inserted += 1

        except Exception as e:
            print(f"❌ Failed {file}: {e}")
            failed += 1

    conn.commit()
    conn.close()

    print("\n📊 SUMMARY")
    print(
        f"Inserted: {inserted} | "
        f"Skipped: {skipped} | "
        f"Failed: {failed} | "
        f"Time: {time.time() - start:.2f}s"
    )

    return inserted

def pipeline():
    inserted_count = main()
    run_role_extraction()
    tag_data(DB_PATH)

    return inserted_count


if __name__ == "__main__":
    pipeline()
