from pathlib import Path
from bs4 import BeautifulSoup
import json
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# --------------------------
# SETTINGS
# --------------------------
BASE_URL = "https://www.ricebowl.my"
HEADERS = {"User-Agent": "Mozilla/5.0"}
RETRY_DELAY = 2  # seconds between requests to avoid blocking

# --------------------------
# PATH
# --------------------------
project_root = Path(__file__).resolve().parent.parent.parent
JSON_DIR = project_root / "data" / "job_data"

# --------------------------
# Fetch description from URL
# --------------------------
def get_full_job_description_from_url(job_url: str) -> str:
    if not job_url or job_url == "Unknown":
        return "Unknown"

    try:
        req = Request(job_url, headers=HEADERS)
        response = urlopen(req, timeout=15)
        html = response.read().decode("utf-8")

        soup = BeautifulSoup(html, "html.parser")
        desc_blocks = soup.find_all("div", class_="job-detail-text")

        full_text = []
        for block in desc_blocks:
            text = block.get_text(strip=True, separator=" ").strip()
            if text:
                full_text.append(text)

        return "\n\n".join(full_text) if full_text else "Unknown"

    except (HTTPError, URLError, Exception):
        return "Unknown"

# --------------------------
# MAIN: Retry ONLY failed descriptions
# --------------------------
def fetch_missing_descriptions():
    print("\n🚀 Fetching missing job descriptions from JSON files...\n")

    if not JSON_DIR.exists():
        print("❌ job_data folder not found!")
        return

    json_files = list(JSON_DIR.glob("*.json"))
    total = len(json_files)
    missing_before = 0
    fixed = 0
    still_missing = 0

    for file in json_files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Only process if description is missing
            if data.get("job_description") == "Unknown":
                missing_before += 1
                job_id = data.get("job_id", "unknown")
                title = data.get("title", "unknown")
                job_url = data.get("job_url")

                print(f"🔁 Retrying: {job_id} | {title}")

                # Fetch new description
                new_desc = get_full_job_description_from_url(job_url)
                time.sleep(RETRY_DELAY)

                if new_desc != "Unknown":
                    # Update and save
                    data["job_description"] = new_desc
                    with open(file, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4, ensure_ascii=False)
                    print(f"✅ SUCCESS: Fetched description for {job_id}")
                    fixed += 1
                else:
                    print(f"❌ FAILED: Still no description for {job_id}")
                    still_missing += 1

        except Exception as e:
            print(f"⚠️ Error reading {file.name}: {e}")

    # --------------------------
    # SUMMARY
    # --------------------------
    print("\n📊 DESCRIPTION FETCH SUMMARY:")
    print(f"Total JSON files: {total}")
    print(f"Missing descriptions before: {missing_before}")
    print(f"✅ Fixed (now have desc): {fixed}")
    print(f"❌ Still missing desc: {still_missing}")
    print("\n✅ Done!\n")

if __name__ == "__main__":
    fetch_missing_descriptions()