import sqlite3
import time
from pathlib import Path

from backend.pipeline.incremental.fetch_new_jobs import fetch_new_jobs
from backend.pipeline.incremental.compare_exisitng import main as compare_existing
from backend.pipeline.incremental.add_jobs_data import main as add_jobs_data
from backend.pipeline.incremental.insert_jobs import pipeline as insert_jobs

# =========================
# PATHS
# =========================
project_root = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = project_root / "data" / "jobs_database.db"

# =========================
# FULL PIPELINE
# =========================
def run_pipeline():
    start = time.time()

    print("\n🚀 STEP 1: Fetch new jobs")
    fetch_new_jobs()

    print("\n🚀 STEP 2: Compare existing jobs")
    compare_existing()

    print("\n🚀 STEP 3: Add jobs data")
    add_jobs_data()

    print("\n🚀 STEP 4: Insert job details (tech stack, etc.)")
    inserted_count = insert_jobs()

    elapsed = time.time() - start

    print("\n🎯 PIPELINE COMPLETE")
    print(f"Inserted: {inserted_count} | ⏱ Total time: {elapsed:.2f}s")

    return inserted_count, elapsed


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    run_pipeline()