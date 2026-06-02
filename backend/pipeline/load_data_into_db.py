import sqlite3
import json
from pathlib import Path
from pydantic import BaseModel

# --------------------------
# Pydantic Model
# --------------------------
class JobListing(BaseModel):
    job_id: str
    title: str
    job_url: str
    company: str
    location: str
    salary: str
    posted_date: str
    actual_posted_date: str
    job_description: str

# --------------------------
# Config
# --------------------------
project_root = Path(__file__).resolve().parent.parent.parent
JSON_FOLDER = project_root / "data" / "job_data"
DB_PATH = project_root / "data" / "jobs_database.db"

# --------------------------
# DELETE OLD DB + CREATE NEW ONE
# --------------------------
def init_db():
    # ✅ DELETE OLD DATABASE FIRST
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("🗑️ Old database deleted")

    # Create new connection (fresh DB)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create fresh table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT,
            job_url TEXT,
            company TEXT,
            location TEXT,
            salary TEXT,
            posted_date TEXT,
            actual_posted_date TEXT,
            job_description TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ New database initialized (job_id as PRIMARY KEY)")

# --------------------------
# Insert one job from JSON
# --------------------------
def insert_job(json_file: Path):
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        job = JobListing(**data)

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR IGNORE INTO jobs
            (job_id, title, job_url, company, location, salary, posted_date, actual_posted_date, job_description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job.job_id,
            job.title,
            job.job_url,
            job.company,
            job.location,
            job.salary,
            job.posted_date,
            job.actual_posted_date,
            job.job_description
        ))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        print(f"❌ Failed to insert {json_file.name}: {str(e)}")
        return False

# --------------------------
# Load ALL JSON to DB
# --------------------------
def load_all():
    if not JSON_FOLDER.exists():
        print("❌ JSON folder not found")
        return

    json_files = list(JSON_FOLDER.glob("*.json"))
    total = len(json_files)
    success = 0
    skipped = 0

    print(f"\n🚀 Starting import from: {JSON_FOLDER}")
    print(f"📂 Found {total} JSON files\n")

    for file in json_files:
        if insert_job(file):
            success += 1
        else:
            skipped += 1

    print(f"\n🗄️ DB Import Summary:")
    print(f"Total: {total} | Inserted: {success} | Duplicates/Skipped: {skipped}")

# --------------------------
# Run
# --------------------------
if __name__ == "__main__":
    init_db()
    load_all()