from pathlib import Path
import re
import sqlite3
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from bs4 import BeautifulSoup

# Configuration
# sortBy=date ensures newest listings appear on page 1 so we can stop early
# once we hit a page where all jobs are already known.
BASE_URL = "https://www.ricebowl.my/jobsearch/{keyword}-jobs?sortBy=date&page={page}"
HEADERS = {"User-Agent": "Mozilla/5.0"}

KEYWORDS = [
    "computer-science",
    "data-science",
    "artificial-intelligence"
]

DELAY = 1.5
MAX_PAGES = 100  # hard safety cap only — real termination is handled by empty-page, early-stop, and wrap-around detection


# =========================
# HELPERS
# =========================

def get_existing_job_ids() -> set:
    """Load all known job_ids from the DB so we can detect when a page is fully old."""
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


def extract_job_ids_from_html(html: str) -> list:
    """Return list of job_id strings found in a ricebowl search-results page."""
    soup = BeautifulSoup(html, "html.parser")
    blocks = soup.find_all("div", id=re.compile(r"website_search-(\d+)"))
    return [block["id"].split("-")[-1] for block in blocks]


def fetch_page(keyword, page):
    url = BASE_URL.format(keyword=keyword, page=page)
    print(f"\n🔎 Fetching: {url}")
    try:
        req = Request(url, headers=HEADERS)
        with urlopen(req) as response:
            status = response.getcode()
            html = response.read().decode("utf-8", errors="ignore")
        print(f"📄 {keyword} | Page {page} | Status {status}")
        return html if status == 200 else None
    except HTTPError as e:
        print(f"❌ {keyword} | Page {page} | HTTP {e.code}")
    except URLError as e:
        print(f"❌ {keyword} | Page {page} | {e.reason}")
    except Exception as e:
        print(f"❌ {keyword} | Page {page} | {e}")
    return None


def clean_html_folder(html_dir: Path):
    if html_dir.exists():
        for file in html_dir.glob("*.html"):
            try:
                file.unlink()
            except Exception as e:
                print(f"⚠️ Could not delete {file.name}: {e}")
    print(f"🧹 Cleaned folder: {html_dir}")


# =========================
# MAIN
# =========================

def fetch_new_jobs():
    start_time = time.time()

    project_root = Path(__file__).resolve().parent.parent.parent.parent
    html_dir = project_root / "data" / "job_sources" / "new"
    html_dir.mkdir(parents=True, exist_ok=True)

    clean_html_folder(html_dir)

    # Load current DB job_ids once — used to detect when a page is fully old
    existing_job_ids = get_existing_job_ids()
    print(f"📂 {len(existing_job_ids)} existing job IDs loaded from DB")

    total_saved = 0

    for keyword in KEYWORDS:
        print(f"\n🔑 Keyword: {keyword}")

        # Track ids seen across pages for this keyword to detect site wrap-around
        seen_ids_this_keyword: set = set()

        for page in range(1, MAX_PAGES + 1):
            html = fetch_page(keyword, page)

            if not html:
                print(f"⚠️  Stopping {keyword} — failed to fetch page {page}")
                break

            page_job_ids = extract_job_ids_from_html(html)

            if not page_job_ids:
                # Empty page means we've gone past the last real page
                print(f"⚠️  Stopping {keyword} — no job blocks on page {page} (past last page)")
                break

            # Detect site wrap-around: page N is showing the same jobs as an earlier page
            if seen_ids_this_keyword and all(jid in seen_ids_this_keyword for jid in page_job_ids):
                print(f"🔄  Stopping {keyword} — page {page} is a duplicate (site wrapped around)")
                break

            new_ids = [jid for jid in page_job_ids if jid not in existing_job_ids]
            print(f"   Page {page}: {len(page_job_ids)} jobs found, {len(new_ids)} new")

            # Save page only if it contains at least one new job
            if new_ids:
                html_file = html_dir / f"{keyword}_page_{page}.html"
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"💾 Saved: {html_file.name}")
                total_saved += 1

            seen_ids_this_keyword.update(page_job_ids)

            # Early stop: sorted by date, so if this page has no new jobs,
            # all following pages (older) will also have none.
            if not new_ids:
                print(f"✅  Stopping {keyword} — page {page} fully known, no older pages needed")
                break

            time.sleep(DELAY)

    elapsed = time.time() - start_time
    print(f"\n📊 Fetch complete | Pages with new jobs saved: {total_saved} | Time: {elapsed:.2f}s")


if __name__ == "__main__":
    fetch_new_jobs()