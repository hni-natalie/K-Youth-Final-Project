from pathlib import Path
import re
import sqlite3
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import json
from bs4 import BeautifulSoup


# =========================
# CONFIG
# =========================
BASE_URL = "https://www.ricebowl.my/jobsearch/{keyword}-jobs?sortBy=date&page={page}"
HEADERS = {"User-Agent": "Mozilla/5.0"}

KEYWORDS = [
    "computer-science",
    "data-science",
    "artificial-intelligence"
]

DELAY = 1.5
MAX_PAGES = 100


# =========================
# HELPERS
# =========================
def get_existing_job_ids() -> set:
    """Load all known job_ids from DB."""
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    db_path = project_root / "data" / "jobs_database.db"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT job_id FROM jobs")
        ids = {str(r[0]) for r in cursor.fetchall()}

        conn.close()
        return ids

    except Exception as e:
        print(f"⚠️ Could not load existing job IDs from DB: {e}")
        return set()


def load_tracker(tracker_path: Path, keywords: list) -> dict:
    if tracker_path.exists():
        with open(tracker_path, "r", encoding="utf-8") as f:
            return json.load(f)

    return {kw: 1 for kw in keywords}


def save_tracker(tracker_path: Path, tracker: dict):
    tracker_path.parent.mkdir(parents=True, exist_ok=True)

    with open(tracker_path, "w", encoding="utf-8") as f:
        json.dump(tracker, f, indent=4)


def extract_job_ids_from_html(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")

    blocks = soup.find_all(
        "div",
        id=re.compile(r"website_search-(\d+)")
    )

    return [
        block["id"].split("-")[-1]
        for block in blocks
    ]


def fetch_page(keyword, page):
    url = BASE_URL.format(
        keyword=keyword,
        page=page
    )

    print(f"\n🔎 Fetching: {url}")

    try:
        req = Request(url, headers=HEADERS)

        with urlopen(req) as response:
            status = response.getcode()
            html = response.read().decode(
                "utf-8",
                errors="ignore"
            )

        print(f"📄 {keyword} | Page {page} | Status {status}")

        return html if status == 200 else None

    except HTTPError as e:
        print(f"❌ {keyword} | Page {page} | HTTP {e.code}")

    except URLError as e:
        print(f"❌ {keyword} | Page {page} | {e.reason}")

    except Exception as e:
        print(f"❌ {keyword} | Page {page} | {e}")

    return None


# =========================
# MAIN
# =========================
def fetch_new_jobs():
    start_time = time.time()

    project_root = Path(__file__).resolve().parent.parent.parent.parent

    html_dir = project_root / "data" / "job_sources"
    tracker_path = project_root / "data" / "tracker" / "page_tracker.json"

    html_dir.mkdir(parents=True, exist_ok=True)

    # Load tracker
    page_tracker = load_tracker(tracker_path, KEYWORDS)
    print(f"📌 Tracker loaded: {page_tracker}")

    existing_job_ids = get_existing_job_ids()
    print(f"📂 Loaded {len(existing_job_ids)} job IDs from DB")

    # =========================
    # PICK ONE KEYWORD ONLY
    # =========================
    min_page = min(page_tracker.values())

    keyword_to_fetch = next(
        kw for kw in KEYWORDS
        if page_tracker[kw] == min_page
    )

    page = page_tracker[keyword_to_fetch]

    print(f"\n🔑 Selected keyword: {keyword_to_fetch}")
    print(f"📄 Fetching page {page}")

    html = fetch_page(keyword_to_fetch, page)

    if not html:
        print(f"❌ Failed to fetch {keyword_to_fetch} page {page}")
        return

    page_job_ids = extract_job_ids_from_html(html)

    if not page_job_ids:
        print(f"⚠️ Empty page for {keyword_to_fetch} page {page}")
        return

    new_ids = [
        job_id for job_id in page_job_ids
        if job_id not in existing_job_ids
    ]

    print(f"📄 Found {len(page_job_ids)} jobs | New: {len(new_ids)}")

    total_saved = 0

    if new_ids:
        html_file = html_dir / f"{keyword_to_fetch}_page_{page}.html"

        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"💾 Saved: {html_file.name}")
        total_saved += 1

    # Update selected keyword only
    page_tracker[keyword_to_fetch] = page + 1
    save_tracker(tracker_path, page_tracker)

    print(f"📌 Tracker updated: {page_tracker}")

    time.sleep(DELAY)

    elapsed = time.time() - start_time

    print(
        f"\n📊 DONE | "
        f"Pages saved: {total_saved} | "
        f"Time: {elapsed:.2f}s"
    )


if __name__ == "__main__":
    fetch_new_jobs()