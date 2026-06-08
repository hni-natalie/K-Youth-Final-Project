from pathlib import Path
import sqlite3
import glob
import time
import pandas as pd
import shutil
from backend.pipeline.bootstrap.extract_job_details import (
    extract_job_info,
)

# =========================
# PATHS
# =========================
project_root = Path(__file__).resolve().parent.parent.parent.parent

NEW_BLOCK_DIR = project_root / "data" / "job_blocks"
CSV_PATH = project_root / "data" / "job_listings.csv"
DB_PATH = project_root / "data" / "jobs_database.db"


# =========================
# CLEAN (optional dev use)
# =========================
def clean_csv_duplicates():
    if CSV_PATH.exists():
        df = pd.read_csv(CSV_PATH)

        before = len(df)
        df = df.drop_duplicates(subset=["job_id"])

        df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

        print(f"🧹 Cleaned CSV duplicates | Before: {before} | After: {len(df)}")


# =========================
# GET EXISTING JOB IDS
# =========================
def get_existing_job_ids():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute("SELECT job_id FROM jobs")
        return {str(r[0]) for r in cur.fetchall()}
    finally:
        conn.close()


# =========================
# APPEND TO CSV
# =========================
def append_to_csv(rows: list[dict]):
    if not rows:
        return

    df_new = pd.DataFrame(rows)

    # If CSV exists → append
    if CSV_PATH.exists():
        df_old = pd.read_csv(CSV_PATH)
        df = pd.concat([df_old, df_new], ignore_index=True)
        df = df.drop_duplicates(subset=["job_id"])
    else:
        df = df_new

    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")


# =========================
# PROCESS JOB BLOCKS
# =========================
def process_new_jobs(existing_job_ids):
    files = glob.glob(str(NEW_BLOCK_DIR / "*.html"))

    rows = []
    skipped = 0
    failed = 0

    for file in files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                html = f.read()

            job = extract_job_info(html)

            # skip duplicates
            if job.job_id in existing_job_ids:
                skipped += 1
                continue

            rows.append(job.model_dump())
            print(f"💾 NEW JOB: {job.title}")

        except Exception as e:
            print(f"❌ Failed: {file} | {e}")
            failed += 1

    append_to_csv(rows)

    return len(rows), skipped, failed


# =========================
# MAIN
# =========================
def main():
    start = time.time()

    existing_job_ids = get_existing_job_ids()
    print(f"📂 Loaded {len(existing_job_ids)} jobs from DB")

    saved, skipped, failed = process_new_jobs(existing_job_ids)

    # optional cleanup
    clean_csv_duplicates()

    print("\n📊 SUMMARY")
    print(
        f"Saved: {saved} | "
        f"Skipped: {skipped} | "
        f"Failed: {failed} | "
        f"Time: {time.time() - start:.2f}s"
    )

    print("\n🧹 Cleaning job_blocks folder...")

    try:
        shutil.rmtree(NEW_BLOCK_DIR)
        print(f"🗑️ Removed folder: {NEW_BLOCK_DIR}")
    except Exception as e:
        print(f"⚠️ Failed to remove job_blocks: {e}")

if __name__ == "__main__":
    main()