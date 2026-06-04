from pathlib import Path
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Configuration
BASE_URL = "https://www.ricebowl.my/jobsearch/{keyword}-jobs?sortBy=relevance&page={page}"
HEADERS = {"User-Agent": "Mozilla/5.0"}  # Mimic browser to avoid blocking

KEYWORDS = ["computer-science", "data-science", "artificial-intelligence"]
MAX_PAGES = 2  # Number of pages to scrape per keyword
DELAY = 1.5    # Delay between requests to avoid overwhelming the server


def fetch_page(keyword, page):
    """
    Fetch raw HTML content from a given URL using urllib (no requests library).
    Returns HTML string if successful, None otherwise.
    """
    url = BASE_URL.format(keyword=keyword, page=page)
    
    try:
        # Create request object with headers (simulate browser request)
        req = Request(url, headers=HEADERS)
        
        # Open the URL and read the response
        with urlopen(req) as response:
            html = response.read().decode('utf-8')  # Convert bytes to UTF-8 string
        
        status = response.getcode()
        print(f"📄 {keyword} | Page {page} | Status {status}")
        
        # Only return HTML if response status is 200 (OK)
        if status != 200:
            return None
        return html

    # Handle HTTP errors (403, 404, 500, etc.)
    except HTTPError as e:
        print(f"[Error] Failed to fetch {keyword} page {page}: HTTP {e.code}")
        return None
    
    # Handle network/connection errors (no internet, DNS failure, etc.)
    except URLError as e:
        print(f"[Error] Failed to fetch {keyword} page {page}: {e.reason}")
        return None
    
    # Catch all other unexpected errors
    except Exception as e:
        print(f"[Error] Failed to fetch {keyword} page {page}: {e}")
        return None


def main():
    start_time = time.time()

    # Set up directory paths
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    html_dir = project_root / "data" / "job_sources"
    html_dir.mkdir(parents=True, exist_ok=True)  # Create folder if it doesn't exist

    # Counters for summary stats
    total_pages = 0
    successful_pages = 0

    # Loop through each keyword and page
    for kw in KEYWORDS:
        for page in range(1, MAX_PAGES + 1):
            total_pages += 1
            html = fetch_page(kw, page)
            
            if html:
                # Save successful HTML response to file
                html_file = html_dir / f"{kw}_page_{page}.html"
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(html)
                print(f"💾 Saved HTML: {html_file}")
                successful_pages += 1
            else:
                print(f"⚠️ Skipped {kw} page {page} due to fetch error")
            
            # Wait before next request to avoid being blocked
            time.sleep(DELAY)

    # Calculate total time taken
    end_time = time.time()
    elapsed = end_time - start_time

    # Print final scraping summary
    print("\n📊 Scraping Summary:")
    print(f"Total: {total_pages} | "
          f"Saved: {successful_pages} | "
          f"Failed: {total_pages - successful_pages} | "
          f"Time taken: {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()