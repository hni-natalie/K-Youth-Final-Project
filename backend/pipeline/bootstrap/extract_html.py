from pathlib import Path
import time
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Configuration
BASE_URL = "https://www.ricebowl.my/jobsearch/{keyword}-jobs?sortBy=relevance&page={page}"
HEADERS = {"User-Agent": "Mozilla/5.0"}

KEYWORDS = ["computer-science", "data-science", "artificial-intelligence"]
MAX_PAGES_PER_RUN = 2
DELAY = 1.5


def fetch_page(keyword, page):
    """
    Fetch raw HTML content from URL.
    Returns HTML string if successful, None otherwise.
    """
    url = BASE_URL.format(keyword=keyword, page=page)

    try:
        req = Request(url, headers=HEADERS)

        with urlopen(req) as response:
            html = response.read().decode("utf-8")
            status = response.getcode()

        print(f"📄 {keyword} | Page {page} | Status {status}")

        if status != 200:
            return None

        return html

    except HTTPError as e:
        print(f"[Error] Failed to fetch {keyword} page {page}: HTTP {e.code}")
        return None

    except URLError as e:
        print(f"[Error] Failed to fetch {keyword} page {page}: {e.reason}")
        return None

    except Exception as e:
        print(f"[Error] Failed to fetch {keyword} page {page}: {e}")
        return None


def load_page_tracker(tracker_file):
    """
    Load page tracker JSON.
    If file doesn't exist, initialize all keywords to page 1.
    """
    if tracker_file.exists():
        with open(tracker_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # Default starting pages
    return {keyword: 1 for keyword in KEYWORDS}


def save_page_tracker(tracker_file, tracker):
    """
    Save updated page tracker to JSON.
    """
    with open(tracker_file, "w", encoding="utf-8") as f:
        json.dump(tracker, f, indent=4)


def main():
    start_time = time.time()

    # Project paths
    project_root = Path(__file__).resolve().parent.parent.parent.parent

    data_dir = project_root / "data"
    html_dir = data_dir / "job_sources"
    tracker_dir = data_dir / "tracker"

    html_dir.mkdir(parents=True, exist_ok=True)
    tracker_dir.mkdir(parents=True, exist_ok=True)

    tracker_file = tracker_dir / "page_tracker.json"

    # Load tracker
    page_tracker = load_page_tracker(tracker_file)

    total_pages = 0
    successful_pages = 0

    # Fetch pages
    for kw in KEYWORDS:
        start_page = page_tracker.get(kw, 1)

        for page in range(start_page, start_page + MAX_PAGES_PER_RUN):
            total_pages += 1

            html = fetch_page(kw, page)

            if html:
                html_file = html_dir / f"{kw}_page_{page}.html"

                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(html)

                print(f"💾 Saved HTML: {html_file}")
                successful_pages += 1

                # Update tracker to NEXT page
                page_tracker[kw] = page + 1

            else:
                print(f"⚠️ Skipped {kw} page {page}")

            time.sleep(DELAY)

    # Save tracker
    save_page_tracker(tracker_file, page_tracker)

    elapsed = time.time() - start_time

    print("\n📊 Scraping Summary:")
    print(
        f"Total: {total_pages} | "
        f"Saved: {successful_pages} | "
        f"Failed: {total_pages - successful_pages} | "
        f"Time taken: {elapsed:.2f} seconds"
    )


if __name__ == "__main__":
    main()