from pathlib import Path
import sqlite3
import time
import pandas as pd

from backend.pipeline.common.extract_role import run_role_extraction
from backend.pipeline.common.extract_tech_stack import tag_data
from backend.pipeline.bootstrap.load_data_into_db import insert_job
from backend.pipeline.common.normalised_tech_stack import run_tech_stack_normalization_pipeline

# =========================
# PATHS
# =========================
project_root = Path(__file__).resolve().parent.parent.parent.parent

CSV_PATH = project_root / "data" / "job_listings.csv"
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
# MAIN PROCESS (CSV VERSION)
# =========================
def main():
    start = time.time()

    if not CSV_PATH.exists():
        print(f"❌ CSV not found: {CSV_PATH}")
        return 0

    df = pd.read_csv(CSV_PATH)

    conn, cursor = get_connection()

    existing_ids = get_existing_job_ids(cursor)
    print(f"📂 Loaded {len(existing_ids)} existing jobs from DB")
    print(f"📄 Loaded {len(df)} rows from CSV")

    inserted = 0
    skipped = 0
    failed = 0

    for _, job in df.iterrows():
        try:
            job_id = str(job["job_id"])

            if job_id in existing_ids:
                skipped += 1
                continue

            insert_job(cursor, job)
            existing_ids.add(job_id)

            print(f"💾 INSERTED: {job['title']}")
            inserted += 1

        except Exception as e:
            print(f"❌ Failed job_id={job.get('job_id')} | {e}")
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

    if inserted_count == 0:
        print("\n⚠️ No new jobs inserted.")
        print("⏭ Skipping enrichment pipeline.")
        return 0

    print("\n🚀 Running role extraction")
    run_role_extraction()

    print("\n🚀 Running tech stack extraction")
    tag_data(DB_PATH)

    print("\n🚀 Running tech stack normalization")
    run_tech_stack_normalization_pipeline()

    return inserted_count


if __name__ == "__main__":
    pipeline()