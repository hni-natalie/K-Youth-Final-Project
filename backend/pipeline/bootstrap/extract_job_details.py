from pathlib import Path
from bs4 import BeautifulSoup
import json
import glob
import re
import unicodedata
import dateparser
import time

# Urllib
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# Pydantic for structure & validation
from pydantic import BaseModel

# --------------------------
# SETTINGS
# --------------------------
BASE_URL = "https://www.ricebowl.my"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# --------------------------
# PYDNANTIC MODEL
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

# ------------------------------
# Field Extractors
# ------------------------------

def extract_job_id(soup: BeautifulSoup) -> str:
    job_block = soup.find("div", id=re.compile(r"website_search-(\d+)"))
    return job_block["id"].split("-")[-1] if job_block else "Unknown"

def extract_job_title(soup: BeautifulSoup) -> str:
    a_tag = soup.find("a", href=re.compile(r"/job/\d+-|/job\?jobId="))
    return a_tag.get_text(strip=True) if a_tag else "Unknown"

def extract_job_url(soup: BeautifulSoup) -> str:
    job_link = soup.find("a", href=re.compile(r"/job/\d+|/job\?jobId=\d+"))
    return BASE_URL + job_link["href"] if job_link else "Unknown"

def extract_company(soup: BeautifulSoup) -> str:
    company_tag = soup.find("h2", id=re.compile(r"companyName\d+"))
    return company_tag.get_text(strip=True) if company_tag else "Unknown"

def extract_location(soup: BeautifulSoup) -> str:
    location_tag = soup.find("a", href=re.compile(r"^/jobsearch/jobs-in"), class_="joblocation-link")
    if not location_tag:
        map_icon = soup.find("svg", {"data-icon": "map-marker-alt"})
        if map_icon:
            parent = map_icon.find_parent()
            if parent:
                return parent.get_text(strip=True)
    return location_tag.get_text(strip=True) if location_tag else "Unknown"

def extract_salary(soup: BeautifulSoup) -> str:
    """
    Extract FULL MYR salary range (e.g., MYR3,000 - MYR3,500)
    Remove ALL text: Per Month, Monthly, 每月, etc.
    """
    salary_icon = soup.find("svg", {"data-icon": "dollar-sign"})
    if not salary_icon:
        return "Unknown"

    parent_span = salary_icon.find_parent("span")
    if not parent_span:
        return "Unknown"

    raw_text = parent_span.get_text(strip=True)

    # Remove all unwanted words
    cleaned = raw_text.replace("每月", "").replace("Per Month", "").replace("Monthly", "").strip()

    # Match FULL salary range (MYR X - MYR Y)
    salary_match = re.search(r"MYR[\d,\s\-]+(?:MYR[\d,\s]+)?", cleaned)

    if salary_match:
        final = salary_match.group(0).strip()
        # Clean messy escaped \, if present
        final = final.replace(r"\,", ",")
        return final

    return "Undisclosed"

def extract_posted_date(soup: BeautifulSoup) -> str:
    posted_div = soup.find("div", class_=lambda c: c and "has-text-grey-light" in c and "is-italic" in c)
    if posted_div and "Posted" in posted_div.get_text():
        time_span = posted_div.find("span")
        return time_span.get_text(strip=True) if time_span else "Unknown"
    return "Unknown"

def get_actual_posted_date(relative_time: str) -> str:
    if relative_time == "Unknown":
        return "Unknown"
    parsed_date = dateparser.parse(relative_time)
    return parsed_date.strftime("%Y-%m-%d") if parsed_date else "Unknown"

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

# ------------------------------
# Utils
# ------------------------------
def clean_json_output_folder(output_dir: Path):
    if output_dir.exists():
        for f in output_dir.glob("*.json"):
            try:
                f.unlink()
            except:
                pass

def sanitize_filename(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    return text[:100]

# ------------------------------
# RETURN PYDANTIC MODEL
# ------------------------------
def extract_job_info(block_html: str) -> JobListing:
    soup = BeautifulSoup(block_html, "html.parser")
    posted_raw = extract_posted_date(soup)
    job_url = extract_job_url(soup)

    return JobListing(
        job_id=extract_job_id(soup),
        title=extract_job_title(soup),
        job_url=job_url,
        company=extract_company(soup),
        location=extract_location(soup),
        salary=extract_salary(soup),
        posted_date=posted_raw,
        actual_posted_date=get_actual_posted_date(posted_raw),
        job_description=get_full_job_description_from_url(job_url)
    )

# ------------------------------
# Run
# ------------------------------
def process_job_file(file_path: str, output_dir: Path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            html = f.read()

        job = extract_job_info(html)
        safe_title = sanitize_filename(job.title)
        filename = f"{job.job_id}_{safe_title}"

        with open(output_dir / f"{filename}.json", "w", encoding="utf-8") as f:
            json.dump(job.model_dump(), f, indent=4, ensure_ascii=False)

        print(f"✅ Saved: {filename}.json")
        return True, job, Path(file_path).name

    except Exception as e:
        print(f"❌ Error: {file_path} | {str(e)}")
        return False, None, Path(file_path).name

def main():
    start_time = time.time()

    root = Path(__file__).resolve().parent.parent.parent.parent
    block_dir = root / "data" / "job_blocks"
    json_dir = root / "data" / "job_data"
    json_dir.mkdir(exist_ok=True)
    clean_json_output_folder(json_dir)

    files = glob.glob(str(block_dir / "*.html"))
    total_found = len(files)
    saved = 0
    failed = 0
    desc_success = 0
    desc_failed_list = []  # Track jobs that failed to get description

    for f in files:
        ok, job, filename = process_job_file(f, json_dir)
        if ok:
            saved +=1
            if job and job.job_description != "Unknown":
                desc_success +=1
            else:
                # Add to failed description list
                desc_failed_list.append(f"{filename} | Title: {job.title} | ID: {job.job_id}")
        else:
            failed +=1

    cost = round(time.time() - start_time,2)
    
    # Summary
    print(f"\n📊 Extraction Summary: ")
    print(f"Found: {total_found} | Saved: {saved} | DescFetched: {desc_success} | Failed: {failed} | Time Taken: {cost} seconds")

    # Show failed descriptions
    if desc_failed_list:
        print(f"\n❌ FAILED TO FETCH DESCRIPTION ({len(desc_failed_list)}):")
        for line in desc_failed_list:
            print(f"  {line}")

if __name__ == "__main__":
    main()