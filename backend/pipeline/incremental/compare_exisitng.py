from pathlib import Path
import sqlite3
import glob
import time

from backend.pipeline.bootstrap.extract_job_data import (
    extract_job_blocks,
    extract_job_title,
    sanitize_filename,
    process_batch_jobs
)
from backend.pipeline.common.config import AI_MODEL, BATCH_SIZE

# =========================
# PATHS
# =========================
project_root = Path(__file__).resolve().parent.parent.parent.parent

HTML_DIR = project_root / "data" / "job_sources" / "new"
NEW_BLOCK_DIR = project_root / "data" / "job_blocks" / "new"
DB_PATH = project_root / "data" / "jobs_database.db"

NEW_BLOCK_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# CLEAN FOLDER (DEV ONLY)
# =========================
def clean_new_output_folder():
    if NEW_BLOCK_DIR.exists():
        for file in NEW_BLOCK_DIR.glob("*.html"):
            try:
                file.unlink()
            except Exception as e:
                print(f"⚠️ Could not delete {file.name}: {e}")

    print("🧹 Cleaned folder: job_blocks/new")


# =========================
# GET EXISTING JOB IDS
# =========================
def get_existing_job_ids():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT job_id FROM jobs")
        rows = cursor.fetchall()
        return {str(r[0]) for r in rows}

    finally:
        conn.close()


# =========================
# COLLECT NEW JOBS FROM HTML
# =========================
def collect_new_job_candidates(existing_job_ids):
    html_files = glob.glob(str(HTML_DIR / "*.html"))

    job_queue = []
    total_jobs = 0
    skipped_existing = 0

    for file in html_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                html = f.read()

            blocks = extract_job_blocks(html)

            print(f"📝 Found {len(blocks)} jobs in {Path(file).name}")

            for block in blocks:
                total_jobs += 1

                job_id = block["id"].split("-")[-1]

                # DB filter here (IMPORTANT)
                if job_id in existing_job_ids:
                    skipped_existing += 1
                    continue

                title = extract_job_title(block)
                job_queue.append((job_id, title, block))

        except Exception as e:
            print(f"❌ Failed {file}: {e}")

    return total_jobs, skipped_existing, job_queue


# =========================
# SAVE ONLY TECH JOBS (USING SHARED PIPELINE)
# =========================
def save_new_tech_jobs(job_queue, existing_job_ids):
    saved = 0
    skipped_non_tech = 0
    skipped_non_tech_titles = []  

    def filter_fn(job_id, title, block, is_tech):
        nonlocal saved, skipped_non_tech, skipped_non_tech_titles

        # skip DB duplicates
        if job_id in existing_job_ids:
            return False

        if not is_tech:
            skipped_non_tech += 1
            skipped_non_tech_titles.append(title) 
            return False

        safe_title = sanitize_filename(title)
        file_path = NEW_BLOCK_DIR / f"{job_id}_{safe_title}.html"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(str(block))

        print(f"💾 NEW TECH JOB: {title}")

        saved += 1
        return True

    process_batch_jobs(
        job_queue=job_queue,
        block_dir=NEW_BLOCK_DIR,
        filter_fn=filter_fn,
        ai_model=AI_MODEL,
        batch_size=BATCH_SIZE
    )

    return saved, skipped_non_tech, skipped_non_tech_titles

# =========================
# MAIN PIPELINE
# =========================
def main():
    start = time.time()

    clean_new_output_folder()

    existing_job_ids = get_existing_job_ids()
    print(f"📂 Loaded {len(existing_job_ids)} jobs from DB")

    total, skipped_existing, job_queue = collect_new_job_candidates(existing_job_ids)

    saved, skipped_non_tech, skipped_non_tech_titles = save_new_tech_jobs(job_queue, existing_job_ids)

    elapsed = time.time() - start

    print("\n🚫 Non-tech jobs skipped:")
    for i, title in enumerate(skipped_non_tech_titles, 1): 
        print(f"{i}. {title}")

    print("\n📊 SUMMARY")
    print(
        f"Total scraped: {total} | "
        f"Existing skipped: {skipped_existing} | "
        f"New tech saved: {saved} | "
        f"Non-tech skipped: {skipped_non_tech} | "
        f"Time: {elapsed:.2f}s"
    )


if __name__ == "__main__":
    main()