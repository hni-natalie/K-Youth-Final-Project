

## 📌 Backend Workflow (Full Pipeline)

This project implements an **end-to-end automated job scraping pipeline** for collecting, filtering, extracting, and storing **tech-related job postings**.

The pipeline consists of **5 main stages**:

---

## 1. Data Source

Raw HTML job listing pages are crawled and saved by:

```plaintext
backend/pipeline/extract_html.py
```

These HTML files are downloaded via URL requests from public job search pages and act as the raw input source for the entire pipeline.

```plaintext
data/job_sources/
```

Example:

```plaintext
computer-science_page_1.html
data-science_page_1.html
artificial-intelligence_page_1.html
```

---

## 2. Extract & Filter Tech Jobs

### Script

```plaintext
backend/pipeline/extract_job_data.py
```

### Purpose

This stage extracts individual job blocks from the raw HTML pages and filters only **technology-related jobs**.

### Features

* Scrapes job blocks from HTML files
* Removes duplicate jobs using **job ID**
* Uses **AI (Gemini)** to classify jobs as:

  * **TECH**
  * **NON-TECH**
* Skips unrelated jobs automatically
* Saves only valid tech jobs

### Output Directory

```plaintext
data/job_blocks/
```

### File Naming Format

```plaintext
{job_id}_{job_title}.html
```

Example:

```plaintext
26592036_Senior_Engineer_Data_Science.html
26472401_Data_Annotator_Mandarin_Speaker.html
```

---

## 3. Extract Full Job Details

### Script

```plaintext
backend/pipeline/extract_job_details.py
```

### Purpose

This stage reads the filtered tech job blocks and extracts **full job information**.

The script visits the job URL and retrieves the complete job description.

### Extracted Fields

The following structured information is extracted:

* Job ID
* Job Title
* Company Name
* Location
* Salary
* Posted Date
* Actual Posted Date
* Full Job Description

### Output Directory

```plaintext
data/job_data/
```

### Output Format

Each job is stored as an individual JSON file.

Example:

```json
{
    "job_id": "26592036",
    "title": "Senior Engineer, Data Science",
    "company": "ABC Company",
    "location": "Kuala Lumpur",
    "salary": "MYR 5,000 - MYR 8,000",
    "posted_date": "2 days ago",
    "actual_posted_date": "2026-05-30",
    "description": "Full job description..."
}
```

---

## 4. Store Data into Database

### Script

```plaintext
backend/pipeline/load_data_into_db.py
```

### Purpose

This stage reads all extracted JSON files and inserts them into a **SQLite database**.

### Database Location

```plaintext
data/jobs_database.db
```

### Features

* Reads all JSON job files
* Inserts structured job data into SQLite
* Prevents duplicate entries
* Supports incremental updates

---

## 4. Extract Tech Stack

### Script

```plaintext
backend/pipeline/extract_job_stack.py
```

### Purpose

This stage uses AI (Gemini) to analyze job descriptions stored in the SQLite database and automatically extract relevant technical skills, tools, and tech stacks.

### Database Update

Extracted tech stack keywords are saved into a new column tech_stack in the existing database.

### Features

* Uses AI to extract tech skills (e.g., Python, React, AWS, Docker, n8n, Zapier)
* Processes jobs in batches to avoid rate limits
* Automatically skips jobs that already have tech stack
* Supports retry for failed AI requests
* Returns none if no technical skills are found
* Updates existing database records directly

---

## 📊 Pipeline Summary Output

### Stage 1 — Fetch Raw HTML Pages

Example output:

```plaintext
📊 Scraping Summary:
Total: 6 | Saved: 6 | Failed: 0 | Time taken: 45.24 seconds
```

### Stage 2 — Extract & Filter Tech Jobs

Example output:

```plaintext
📊 Extraction Summary:
Found: 180 | Saved: 138 | Duplicates: 11 | Non-tech skipped: 31 | Failed: 0 | Time Taken: 24.73 seconds
```

### Stage 3 — Extract Full Job Details

Example output:

```plaintext
📊 Extraction Summary:
Found: 138 | Saved: 138 | DescFetched: 134 | DescFailed: 4 | Failed: 0 | Time Taken: 378.75 seconds
```

### Stage 4 — Store into Database

Example output:

```plaintext
🗄️ Database Summary:
Total: 138 | Inserted: 138 | Duplicates/Skipped: 0
```

### Stage 5 — Extract Tech Stack

Example output:

```plaintext
=== Processing Batch 10 ===
AFC is enabled with max remote calls: 10.
HTTP Request: POST https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent "HTTP/1.1 200 OK"
Analyzed Job 26503312: Java, Python, AWS
Analyzed Job 26512849: none
Analyzed Job 26472784: Python, n8n, Zapier
Analyzed Job 26498274: Python, PyTorch, 3D Computer Vision

[INFO] All jobs processed ✅
```

---

## 📂 Folder Structure

```plaintext
├── backend
│   ├── Search_API.md
│   ├── Stats_API.md
│   ├── api
│   │   ├── __init__.py
│   │   ├── main.py
│   │   └── routes
│   │       ├── search_routes.py
│   │       └── stats_routes.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── config.py                   # Store Shared Global Variable 
│   │   └── database
│   │       ├── chat.py
│   │       ├── company_stats.py
│   │       ├── connection.py
│   │       ├── location_stats.py
│   │       ├── role_stats.py
│   │       ├── salary_stats.py
│   │       ├── search.py
│   │       ├── tech_stack_stats.py
│   │       └── trend_stats.py
│   ├── pipeline
│   │   ├── __init__.py
│   │   ├── bootstrap
│   │   │   ├── __init__.py
│   │   │   ├── extract_html.py
│   │   │   ├── extract_job_data.py
│   │   │   ├── extract_job_details.py
│   │   │   └── load_data_into_db.py
│   │   ├── common
│   │   │   ├── __init__.py
│   │   │   ├── config.py
│   │   │   ├── extract_role.py
│   │   │   ├── extract_tech_stack.py
│   │   │   ├── fetch_job_desc.py
│   │   │   └── prompt_model.py
│   │   └── incremental
│   │       ├── __init__.py
│   │       ├── add_jobs_data.py
│   │       ├── compare_exisitng.py
│   │       ├── fetch_new_jobs.py
│   │       ├── insert_jobs.py
│   │       └── run.py
│   ├── pyproject.toml
│   ├── utils
│   │   ├── __init__.py
│   │   └── error_handlers.py
│
├── pyproject.toml
└── uv.lock
│
data/
├── job_sources/                 # Raw HTML pages
├── job_blocks/                  # Filtered tech jobs (HTML)
├── job_data/                    # Structured JSON data
├── metadata/                    # Structured JSON data
|     └── page_tracker.json      # Keep track on the new page number 
└── jobs_database.db             # SQLite database
```

---

## ⚙️ How to Run

### 1. Filter & Save Tech Jobs

Run:

```bash
uv run ./backend/src/extract_job_data.py
```

This will:

* Read raw HTML job pages
* Remove duplicate jobs
* Filter non-tech jobs using AI
* Save tech-related job blocks

---

### 2. Extract Full Job Details

Run:

```bash
uv run ./backend/src/extract_job_details.py
```

This will:

* Read filtered tech jobs
* Visit job URLs
* Extract complete job details
* Save structured JSON output

---

### 3. Load Data into Database

Run:

```bash
uv run ./backend/src/load_data_into_db.py
```

This will:

* Read all JSON files
* Insert job data into SQLite
* Skip duplicates automatically

---

### 4. Retry failed job descriptions

Run:

```bash
uv run ./backend/src/fetch_job_desc.py
```

---

### 3. Extract tech stack from job descriptions

Run:

```bash
uv run ./backend/src/extract_tech_stack.py
```

This will:

* Read job description 
* Extract tech stack and store in db

---

## 🧾 Key Features

- ✅ AI-powered tech job filtering
- ✅ Automatic duplicate removal
- ✅ Full job details extraction
- ✅ Job description retry mechanism
- ✅ Structured JSON output
- ✅ SQLite database storage
- ✅ AI-powered tech stack extraction
- ✅ Modular, maintainable architecture
- ✅ Testable data pipeline
- ✅ Ready for backend API integration