from pathlib import Path
import json
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# Configuration
BASE_URL = "https://www.ricebowl.my/jobsearch/{keyword}-jobs?sortBy=relevance&page={page}"
HEADERS = {"User-Agent": "Mozilla/5.0"}

KEYWORDS = [
    "computer-science",
    "data-science",
    "artificial-intelligence"
]

DELAY = 1.5


def load_page_tracker(tracker_file):
    """
    Load last scraped page number.
    Default to page 3 if file doesn't exist.
    """
    if tracker_file.exists():
        with open(tracker_file, "r") as f:
            return json.load(f)

    return {keyword: 3 for keyword in KEYWORDS}


def save_page_tracker(tracker_file, tracker):
    """
    Save updated page tracker.
    """
    with open(tracker_file, "w") as f:
        json.dump(tracker, f, indent=4)


def fetch_page(keyword, page):
    url = BASE_URL.format(keyword=keyword, page=page)

    print(f"\n🔎 Fetching: {url}")

    try:
        req = Request(url, headers=HEADERS)

        with urlopen(req) as response:
            status = response.getcode()
            html = response.read().decode("utf-8", errors="ignore")

        print(f"📄 {keyword} | Page {page} | Status {status}")

        if status != 200:
            return None

        return html

    except HTTPError as e:
        print(f"❌ {keyword} | Page {page} | HTTP {e.code}")
        return None

    except URLError as e:
        print(f"❌ {keyword} | Page {page} | {e.reason}")
        return None

    except Exception as e:
        print(f"❌ {keyword} | Page {page} | {e}")
        return None


def clean_html_folder(html_dir: Path):
    """DEV ONLY: clear previous scraped HTML files"""
    if html_dir.exists():
        for file in html_dir.glob("*.html"):
            try:
                file.unlink()
            except Exception as e:
                print(f"⚠️ Could not delete {file.name}: {e}")

    print(f"🧹 Cleaned folder: {html_dir}")


def fetch_new_jobs():
    start_time = time.time()

    project_root = Path(__file__).resolve().parent.parent.parent.parent

    html_dir = project_root / "data" / "job_sources" / "new"
    html_dir.mkdir(parents=True, exist_ok=True)

    metadata_dir = project_root / "data" / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)

    clean_html_folder(html_dir)

    tracker_file = metadata_dir / "page_tracker.json"
    page_tracker = load_page_tracker(tracker_file)

    successful_fetches = 0

    for keyword in KEYWORDS:
        next_page = page_tracker[keyword] + 1

        html = fetch_page(keyword, next_page)

        if html:
            html_file = html_dir / f"{keyword}_page_{next_page}.html"

            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html)

            print(f"💾 Saved HTML: {html_file}")

            page_tracker[keyword] = next_page
            successful_fetches += 1

        else:
            print(f"⚠️ Failed {keyword} page {next_page}")

        time.sleep(DELAY)

    save_page_tracker(tracker_file, page_tracker)

    elapsed = time.time() - start_time

    print("\n📊 Incremental Fetch Summary:")
    print(
        f"Saved: {successful_fetches} | "
        f"Failed: {len(KEYWORDS) - successful_fetches} | "
        f"Time taken: {elapsed:.2f} seconds"
    )


if __name__ == "__main__":
    fetch_new_jobs()