from pathlib import Path
from bs4 import BeautifulSoup
import re
import glob
import os
import time
import unicodedata
from backend.pipeline.common.prompt_model import prompt_model
from backend.pipeline.common.config import AI_MODEL, BATCH_SIZE

# CONFIG
# AI_MODEL = "llama3.1"

def extract_job_blocks(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.find_all(
        "div",
        id=re.compile(r"website_search-(\d+)")
    )


def extract_job_title(block):
    a_tag = block.find("a", href=re.compile(r"/job/\d+-|/job\?jobId="))
    if not a_tag:
        return "Unknown"
    return a_tag.get_text(strip=True)


def sanitize_filename(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r'[<>:"/\\|?*]', '', text)
    text = re.sub(r"\s+", "_", text.strip())
    return text[:100]


def create_tech_job_prompt(batch_jobs: list) -> str:
    prompt = """
Classify each job title below as TECH-RELATED (YES/NO only, no extra text).

Tech-related jobs include any role primarily involving technology, 
computing, programming, data analysis, machine learning, 
AI, Artificial Intelligence, IT systems, cloud, cybersecurity, 
engineering, tester, or technical infrastructure. 

Non-tech roles are administrative, finance, 
HR, sales, marketing, operations, lab, or field work.

Return ONLY a comma-separated list of YES/NO. Example: YES,NO,YES
Job Titles:
"""
    for idx, (job_id, title) in enumerate(batch_jobs, 1):
        prompt += f"{idx}. {title}\n"
    prompt += "Response:"
    return prompt


def parse_ai_response(response: str, batch_size: int) -> list[bool]:
    try:
        res = [x.strip().upper() for x in response.split(",")]
        return [x == "YES" for x in res[:batch_size]]
    except:
        return [True] * batch_size


def setup_directories() -> tuple[Path, Path]:
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    html_dir = project_root / "data" / "job_sources"
    block_dir = project_root / "data" / "job_blocks"
    block_dir.mkdir(parents=True, exist_ok=True)
    return html_dir, block_dir


def collect_unique_jobs(html_dir: Path) -> tuple[int, int, set, list]:
    total_job_blocks = 0
    duplicate_count = 0
    seen_job_ids = set()
    duplicate_ids = set() 
    job_queue = []

    html_files = glob.glob(str(html_dir / "*.html"))
    for html_file in html_files:
        try:
            with open(html_file, "r", encoding="utf-8") as f:
                html = f.read()

            job_blocks = extract_job_blocks(html)
            print(f"📝 Found {len(job_blocks)} jobs in {Path(html_file).name}")
            total_job_blocks += len(job_blocks)

            for block in job_blocks:
                job_id = block["id"].split("-")[-1]
                if job_id in seen_job_ids:
                    duplicate_count += 1
                    duplicate_ids.add(job_id) 
                    continue
                seen_job_ids.add(job_id)
                job_title = extract_job_title(block)
                job_queue.append((job_id, job_title, block))

        except Exception as e:
            print(f"❌ Failed to process {html_file}: {e}")

    return total_job_blocks, duplicate_count, duplicate_ids, job_queue 


def process_batch_jobs(
    job_queue: list,
    block_dir: Path,
    filter_fn=None,
    ai_model=AI_MODEL,
    batch_size=BATCH_SIZE
) -> tuple[int, int, list]:

    saved_job_blocks = 0
    non_tech_skipped = 0
    skipped_job_titles = []

    for i in range(0, len(job_queue), batch_size):
        batch = job_queue[i:i + batch_size]
        batch_data = [(j[0], j[1]) for j in batch]

        prompt = create_tech_job_prompt(batch_data)
        ai_res = prompt_model(ai_model, prompt)
        print(f"AI RES: {ai_res}")

        if "Error" in ai_res:
            print(f"⚠️ AI Service Error: {ai_res}")
            tech_list = [True] * len(batch)
        else:
            tech_list = parse_ai_response(ai_res, len(batch))

        for is_tech, job in zip(tech_list, batch):
            job_id, title, block = job

            # ❗ default behavior fallback (bootstrap pipeline)
            if filter_fn is None:
                if not is_tech:
                    non_tech_skipped += 1
                    continue

                safe_title = sanitize_filename(title)
                file_path = block_dir / f"{job_id}_{safe_title}.html"

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(str(block))

                saved_job_blocks += 1
                continue

            # ❗ incremental pipeline uses filter_fn
            result = filter_fn(job_id, title, block, is_tech)

            if not is_tech:
                non_tech_skipped += 1

            if result:
                saved_job_blocks += 1
                skipped_job_titles.append(title)

    return saved_job_blocks, non_tech_skipped, skipped_job_titles


def print_summary(
    total_job_blocks: int,
    saved_job_blocks: int,
    duplicate_count: int,
    non_tech_skipped: int,
    elapsed: float,
    skipped_job_titles: list,
    duplicate_ids: set  
):
    print("\n📊 Extraction Summary:")
    print(
        f"Found: {total_job_blocks} | "
        f"Saved: {saved_job_blocks} | "
        f"Duplicates: {duplicate_count} | "
        f"Non-tech skipped: {non_tech_skipped} | "
        f"Failed: {total_job_blocks - saved_job_blocks - duplicate_count - non_tech_skipped} | "
        f"Time Taken: {elapsed:.2f} seconds"
    )

    if skipped_job_titles:
        print("\n🚫 Non-tech jobs skipped:")
        for idx, title in enumerate(skipped_job_titles, 1):
            print(f"  {idx}. {title}")

    if duplicate_ids:
        print("\n⚠️ Duplicated Job IDs:")
        print(", ".join(sorted(duplicate_ids)))


def clean_output_folder(block_dir: Path):
    if block_dir.exists():
        for file in block_dir.glob("*.html"):
            try:
                file.unlink()
            except Exception as e:
                print(f"⚠️ Could not delete {file.name}: {e}")
    print("🧹 Cleaned output folder: job_blocks")


def main():
    start_time = time.time()

    html_dir, block_dir = setup_directories()

    clean_output_folder(block_dir)

    total_job_blocks, duplicate_count, duplicate_ids, job_queue = collect_unique_jobs(html_dir)

    saved_job_blocks, non_tech_skipped, skipped_job_titles = process_batch_jobs(job_queue, block_dir)

    elapsed = time.time() - start_time
    print_summary(
        total_job_blocks,
        saved_job_blocks,
        duplicate_count,
        non_tech_skipped,
        elapsed,
        skipped_job_titles,
        duplicate_ids
    )

if __name__ == "__main__":
    main()
