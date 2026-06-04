from pathlib import Path
import sqlite3
import glob
import time
import json

from backend.pipeline.bootstrap.extract_job_details import (
    extract_job_info,
    sanitize_filename
)

# =========================
# PATHS
# =========================
project_root = Path(__file__).resolve().parent.parent.parent.parent

NEW_BLOCK_DIR = project_root / "data" / "job_blocks" / "new"
NEW_JSON_DIR = project_root / "data" / "job_data" / "new"
DB_PATH = project_root / "data" / "jobs_database.db"

NEW_JSON_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# CLEAN (DEV ONLY)
# =========================
def clean_new_json_folder():
    if NEW_JSON_DIR.exists():
        for f in NEW_JSON_DIR.glob("*.json"):
            f.unlink()
    print("🧹 Cleaned job_data/new")


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
# PROCESS NEW JOB BLOCKS
# =========================
def process_new_jobs(existing_job_ids):
    files = glob.glob(str(NEW_BLOCK_DIR / "*.html"))

    saved = 0
    skipped = 0
    failed = 0

    for file in files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                html = f.read()

            job = extract_job_info(html)

            # skip if already in DB
            if job.job_id in existing_job_ids:
                skipped += 1
                continue

            safe_title = sanitize_filename(job.title)
            filename = f"{job.job_id}_{safe_title}.json"

            with open(NEW_JSON_DIR / filename, "w", encoding="utf-8") as f:
                json.dump(job.model_dump(), f, indent=4, ensure_ascii=False)

            print(f"💾 NEW JOB DATA: {job.title}")
            saved += 1

        except Exception as e:
            print(f"❌ Failed: {file} | {e}")
            failed += 1

    return saved, skipped, failed


# =========================
# MAIN
# =========================
def main():
    start = time.time()

    clean_new_json_folder()

    existing_job_ids = get_existing_job_ids()
    print(f"📂 Loaded {len(existing_job_ids)} existing jobs")

    saved, skipped, failed = process_new_jobs(existing_job_ids)

    print("\n📊 SUMMARY")
    print(
        f"Saved: {saved} | "
        f"Skipped (existing): {skipped} | "
        f"Failed: {failed} | "
        f"Time: {time.time() - start:.2f}s"
    )


if __name__ == "__main__":
    main()