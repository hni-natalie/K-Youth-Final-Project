from pathlib import Path
from bs4 import BeautifulSoup
import json
import glob
import re
import unicodedata
import dateparser
import time
import pandas as pd
import shutil
from pydantic import BaseModel

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


# --------------------------
# SETTINGS
# --------------------------
BASE_URL = "https://www.ricebowl.my"
HEADERS = {"User-Agent": "Mozilla/5.0"}


# --------------------------
# PYDANTIC MODEL
# --------------------------
class JobListing(BaseModel):
    job_id: str
    title: str
    job_url: str
    company: str
    location: str

    salary_min: float | None = None
    salary_max: float | None = None
    salary_mean: float | None = None

    actual_posted_date: str
    job_description: str


# ------------------------------
# FIELD EXTRACTORS
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
    location_tag = soup.find(
        "a",
        href=re.compile(r"^/jobsearch/jobs-in"),
        class_="joblocation-link"
    )

    if not location_tag:
        map_icon = soup.find("svg", {"data-icon": "map-marker-alt"})
        if map_icon:
            parent = map_icon.find_parent()
            if parent:
                return parent.get_text(strip=True)

    return location_tag.get_text(strip=True) if location_tag else "Unknown"


def extract_salary(soup: BeautifulSoup):
    salary_icon = soup.find("svg", {"data-icon": "dollar-sign"})
    if not salary_icon:
        return None, None, None

    parent_span = salary_icon.find_parent("span")
    if not parent_span:
        return None, None, None

    raw_text = parent_span.get_text(strip=True)

    cleaned = (
        raw_text.replace("每月", "")
        .replace("Per Month", "")
        .replace("Monthly", "")
        .replace(r"\,", ",")
        .strip()
    )

    nums = re.findall(r"[\d,]+", cleaned)
    if not nums:
        return None, None, None

    salaries = [float(n.replace(",", "")) for n in nums]

    if len(salaries) >= 2:
        salary_min = salaries[0]
        salary_max = salaries[1]
    else:
        salary_min = salary_max = salaries[0]

    salary_mean = (salary_min + salary_max) / 2

    return salary_min, salary_max, salary_mean


def extract_posted_date(soup: BeautifulSoup) -> str:
    posted_div = soup.find(
        "div",
        class_=lambda c: c and "has-text-grey-light" in c and "is-italic" in c
    )

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
# UTILS
# ------------------------------
def sanitize_filename(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    return text[:100]


# ------------------------------
# JOB PARSE
# ------------------------------
def extract_job_info(block_html: str) -> JobListing:
    soup = BeautifulSoup(block_html, "html.parser")

    posted_raw = extract_posted_date(soup)
    job_url = extract_job_url(soup)

    salary_min, salary_max, salary_mean = extract_salary(soup)

    return JobListing(
        job_id=extract_job_id(soup),
        title=extract_job_title(soup),
        job_url=job_url,
        company=extract_company(soup),
        location=extract_location(soup),
        salary_min=salary_min,
        salary_max=salary_max,
        salary_mean=salary_mean,
        actual_posted_date=get_actual_posted_date(posted_raw),
        job_description=get_full_job_description_from_url(job_url)
    )


# ------------------------------
# MAIN
# ------------------------------
def main():
    start_time = time.time()

    print("\n🚀 Starting job extraction pipeline...\n")

    root = Path(__file__).resolve().parent.parent.parent.parent
    block_dir = root / "data" / "job_blocks"
    csv_path = root / "data" / "job_listings.csv"

    if not block_dir.exists():
        print(f"❌ Input folder not found: {block_dir}")
        return

    files = glob.glob(str(block_dir / "*.html"))
    print(f"🔍 Found {len(files)} HTML files")

    jobs = []
    desc_failed_indexes = []

    # --------------------------
    # STEP 1: PARSE JOBS
    # --------------------------
    for idx, file_path in enumerate(files, start=1):
        print(f"\n[{idx}/{len(files)}] Processing {Path(file_path).name}")

        with open(file_path, "r", encoding="utf-8") as f:
            html = f.read()

        job = extract_job_info(html)
        job_dict = job.model_dump()

        print(f"✅ {job.job_id} | {job.title}")

        if job_dict["job_description"] == "Unknown":
            desc_failed_indexes.append(idx)

        jobs.append(job_dict)

    # --------------------------
    # STEP 2: RETRY DESCRIPTIONS (IN-PLACE)
    # --------------------------
    if desc_failed_indexes:
        print(f"\n⚠️ Missing descriptions: {len(desc_failed_indexes)}")
        print("🔁 Retrying directly via extract_job_desc...\n")

        for job in jobs:
            if job["job_description"] != "Unknown":
                continue

            print(f"🔁 Fetching: {job['job_id']}")

            new_desc = get_full_job_description_from_url(job["job_url"])

            if new_desc != "Unknown":
                job["job_description"] = new_desc
                print(f"✅ Fixed: {job['job_id']}")
            else:
                print(f"❌ Still missing: {job['job_id']}")

    # --------------------------
    # STEP 3: FINAL CLEANUP CHECK
    # --------------------------
    still_missing = [j for j in jobs if j["job_description"] == "Unknown"]

    print("\n📊 FINAL CHECK")
    print(f"Total jobs: {len(jobs)}")
    print(f"Still missing: {len(still_missing)}")

    # --------------------------
    # STEP 4: SAVE CSV
    # --------------------------
    pd.DataFrame(jobs).to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"\n💾 CSV saved: {csv_path}")

    # --------------------------
    # STEP 5: DELETE FOLDER ONLY IF CLEAN
    # --------------------------
    if not still_missing:
        print("🧹 All descriptions resolved. Deleting job_blocks folder...")

        try:
            shutil.rmtree(block_dir)
            print(f"🗑️ Removed: {block_dir}")
        except Exception as e:
            print(f"⚠️ Cleanup failed: {e}")
    else:
        print("🚫 Skipping deletion due to missing descriptions.")

    elapsed = round(time.time() - start_time, 2)

    print(f"\n🎯 DONE | Jobs: {len(jobs)} | Missing: {len(still_missing)} | Time: {elapsed}s")


if __name__ == "__main__":
    main()