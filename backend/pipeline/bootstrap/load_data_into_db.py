import sqlite3
from pathlib import Path
import pandas as pd

# --------------------------
# Config
# --------------------------
project_root = Path(__file__).resolve().parent.parent.parent.parent
CSV_FILE = project_root / "data" / "job_listings.csv"
DB_PATH = project_root / "data" / "jobs_database.db"

# --------------------------
# Init DB
# --------------------------
def init_db():
    if DB_PATH.exists():
        DB_PATH.unlink()
        print("🗑️ Old database deleted")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT,
            job_url TEXT,
            company TEXT,
            location TEXT,
            salary_min REAL,
            salary_max REAL,
            salary_mean REAL,
            actual_posted_date TEXT,
            job_description TEXT
        )
    ''')

    conn.commit()
    conn.close()

    print("✅ New database initialized")


# --------------------------
# Insert from DataFrame row
# --------------------------
def insert_job(cursor, row):
    cursor.execute('''
        INSERT OR IGNORE INTO jobs (
            job_id, title, job_url, company, location,
            salary_min, salary_max, salary_mean,
            actual_posted_date, job_description
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        row["job_id"],
        row["title"],
        row["job_url"],
        row["company"],
        row["location"],
        row["salary_min"],
        row["salary_max"],
        row["salary_mean"],
        row["actual_posted_date"],
        row["job_description"]
    ))


# --------------------------
# Load CSV → DB
# --------------------------
def load_csv_to_db():
    if not CSV_FILE.exists():
        print(f"❌ CSV not found: {CSV_FILE}")
        return

    df = pd.read_csv(CSV_FILE)
    total = len(df)

    print(f"\n🚀 Loading CSV: {CSV_FILE}")
    print(f"📂 Total rows: {total}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    inserted = 0
    skipped = 0

    for _, row in df.iterrows():
        try:
            insert_job(cursor, row)
            inserted += 1
        except Exception as e:
            skipped += 1
            print(f"❌ Failed row {row.get('job_id')} | {e}")

    conn.commit()
    conn.close()

    print(f"\n🗄️ DB IMPORT SUMMARY | Total: {total} | Inserted: {inserted} | Skipped: {skipped}")


# --------------------------
# Run
# --------------------------
if __name__ == "__main__":
    init_db()
    load_csv_to_db()