# 🚀 SkillScope — AI-Powered Job Market Analytics Platform

## 📌 Project Overview
SkillScope is an AI-powered job market analytics platform designed to help users understand the current technology job market and evaluate how well their skills align with industry demand.

The platform continuously collects real-world job postings from RiceBowl, processes and structures the data through an automated pipeline, and transforms raw job listings into actionable labor market insights.

Using AI-driven analysis, SkillScope provides users with:
- 📈 Job Market Trends — identify the most in-demand technologies, roles, and skills
- 💰 Salary Insights — analyze salary distributions across job categories
- 📍 Location Analytics — discover hiring hotspots and regional job demand
- 🏢 Company Hiring Trends — understand which companies are actively recruiting
- 🧠 AI Resume Matching — upload a resume and evaluate how well it aligns with current market requirements

The goal of SkillScope is to bridge the gap between job seekers and market expectations by helping users make better career decisions through data-driven insights.

---

## 🎯 Problem Statement

Many job seekers struggle to understand:

- Which technical skills are currently in demand
- What salary range they should expect
- Which locations have better job opportunities
- Whether their resume matches current industry expectations

Traditional job platforms focus mainly on job listings, but provide limited analytical insights into the broader job market.

SkillScope addresses this problem by transforming job postings into structured intelligence using data engineering, AI, and analytics.

--- 

## 🎯 Target Users

SkillScope is designed for:

- 👨‍🎓 Students exploring tech careers
- 💼 Job seekers preparing for employment
- 🔄 Career switchers entering technology fields
- 📊 Researchers analyzing labor market trends
- 🏫 Universities monitoring graduate employability

---

## 💡 Key Objectives

SkillScope aims to:

1. Automate job market data collection from public job platforms
2. Analyze hiring demand trends across technologies and job roles
3. Provide salary and location intelligence
4. Extract technical skill requirements using AI
5. Recommend skill improvements through resume matching
6. Help users benchmark themselves against current market expectations

---

## 🏗️ System Architecture

SkillScope follows an end-to-end data pipeline architecture, transforming raw job listings into structured analytics and AI-powered recommendations.

### Data Flow

The overall workflow follows the structure below:

```plaintext
    RiceBowl Job Listings
            ↓
     HTML Scraping
            ↓
  Tech Job Classification (AI)
            ↓
  Job Detail Extraction
            ↓
   Structured JSON Output
            ↓
      SQLite Database
            ↓
   Data Analytics API
            ↓
Frontend Dashboard / Resume Analysis
```

### End-to-End Pipeline

#### Step 1 — Raw Job Collection

Raw HTML pages are fetched from RiceBowl job search results and stored locally.

Input

```text
RiceBowl Job Search URLs
```

Processing

- Sends HTTP requests to RiceBowl
- Downloads HTML job listing pages
- Stores raw pages for reproducibility

Output

```plaintext
data/job_sources/
```

Example:

```text
computer-science_page_4.html
data-science_page_4.html
artificial-intelligence_page_4.html
```

#### Step 2 — AI Tech Job Filtering

The system extracts job blocks and uses AI to determine whether a job belongs to the technology domain.

Input

```
Raw HTML job pages
```

Processing

- Parse job listing blocks
- Remove duplicates via job ID
- AI classification using Gemini
- Filter non-tech jobs

Output

```
data/job_blocks/
```

#### Step 3 — Full Job Information Extraction

Each filtered tech job is processed to extract detailed job information.

Input

```
Filtered tech job blocks
```

Processing

- Extract title
- Extract company
- Extract salary
- Extract location
- Extract posting date
- Visit job URL
- Retrieve full job description

Output

```
data/job_data/
```

Format:

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

#### Step 4 — Database Storage

Structured job data is inserted into a SQLite database.

Input
```
Structured JSON files
```

Processing

- Read extracted JSON
- Insert records into database
- Skip duplicates
- Support incremental updates

Output
```
data/jobs_database.db
```

#### Step 5 — AI Data Enrichment

AI models enrich job data with additional intelligence.

#### Role Classification

Maps job titles into standardized tech categories.

Example:
```
"Junior Backend Engineer" → "Backend Engineer"
```

#### Tech Stack Extraction

Extracts technical skills directly from job descriptions.

Example:
```
Python, SQL, AWS, Docker, TensorFlow
```

#### Resume Alignment (Future Feature)

Users can upload resumes to compare against market demand and identify skill gaps.

---

## 📂 Module Breakdown

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
├──data/
|   ├── job_sources/                 # Raw HTML pages
|   ├── job_blocks/                  # Filtered tech jobs (HTML)
|   ├── job_data/                    # Structured JSON data
|   ├── metadata/                    # Structured JSON data
|     └── page_tracker.json      # Keep track on the new page number 
└── jobs_database.db             # SQLite database
├── docker-compose.yml
├── frontend
│   ├── API_CONTRACT.md
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── src
│   │   ├── app.py
│   │   ├── static
│   │   │   └── services
│   │   │       └── api.js
│   │   └── templates
│   │       ├── chat_page.html
│   │       ├── dashboard.html
│   │       └── stats.html
│   └── uv.lock
└── tests
    └── test_data_counts.py
```

---

## 🛠 Dependencies & Environment Setup

Before running SkillScope, ensure the following dependencies are installed on your machine.

### Required Software
1. Install Docker Desktop

SkillScope uses Docker Compose to run the frontend and backend services.

Download and install Docker Desktop:

- Windows / macOS: Install Docker Desktop from the official website
- Linux: Install Docker Engine and Docker Compose

After installation, verify Docker is running:

```
docker --version
docker compose version
```

You should see version numbers returned.

Example:

```
Docker version 28.x.x
Docker Compose version v2.x.x
```

Ensure Docker Desktop is running before starting the project.

--- 

## ⚙️ Setup & Installation

Follow the steps below to run SkillScope locally.

### 1. Clone the Repository
```
git clone <your-repository-url>
cd K-Youth-Final-Project
```

--- 

### 2. Configure Environment Variables

Copy the example environment file:

```
cp .env.example .env
```

Then update the environment variables in .env if necessary.

---

### 3. Run the Application with Docker

Build and start all services using Docker Compose:

```
docker compose up --build
```

This will:

- Build backend containers
- Install required dependencies
- Start the FastAPI backend
- Mount project files for development
- Run the application environment locally

To run in detached mode:

```
docker compose up -d --build
```

To stop containers:

```
docker compose down
```

---

### 4. Access the Application

Once the containers are running, you can access the system locally through your browser.

#### Frontend (Main Application)

```text
http://localhost:8000
```

This is the main SkillScope web application where users can:

- Explore job market analytics
- View salary trends
- Analyze hiring demand by location
- Explore trending tech stacks and roles
- Upload resumes for AI-powered job market alignment analysis

#### Backend API (FastAPI)

```text
http://localhost:8001
```

---

## ✨ Features

SkillScope provides an end-to-end job market analytics platform powered by web scraping, data processing, and AI-driven insights.

### 1. Job Market Analytics Dashboard

Analyze the current technology job market using real job postings collected from RiceBowl.

Features include:

- Salary trend analysis
- Hiring demand insights
- Location-based job distribution
- Company hiring statistics
- Tech stack demand tracking
- Job role trend analysis

This enables users to understand what skills and roles are currently in demand.

---

### 2. Automated Job Data Pipeline

SkillScope includes a fully automated backend pipeline for collecting and processing job market data.

Pipeline capabilities:

- Scrapes raw job listings from RiceBowl
- Filters technology-related jobs using AI
- Extracts structured job details
- Stores data into a SQLite database
- Performs incremental updates for newly posted jobs
- Automatically removes duplicates

This ensures the system continuously reflects current market trends.

----

### 3. AI-Powered Tech Job Filtering

An AI model is used to classify job postings into:

- Tech-related jobs
- Non-tech jobs

This reduces noise in the dataset and ensures only relevant technology jobs are included in the analysis.

---

### 4. Tech Stack Extraction

SkillScope automatically extracts technical skills and technologies from job descriptions using AI.

Examples of extracted technologies:

- Python
- SQL
- React

This helps users identify the most demanded technical skills in the market.

----

### 5. Salary Trend Analysis

Users can explore salary trends across different roles and technologies.

The system analyzes:

- Salary distribution
- Minimum and maximum salary ranges
- Average market salary
- Role-based salary trends

This helps users benchmark compensation expectations.

----

### 6. Location-Based Market Insights

SkillScope analyzes where technology hiring demand is concentrated.

Users can view:

- Top hiring cities
- Regional hiring demand
- Job concentration by location
- Location-specific salary trends

This helps job seekers identify high-opportunity areas.

---

### 7. Resume-to-Market Alignment (AI Recommendation)

Users can upload their resume and compare it against current job market demands.

The AI system evaluates:

- Resume skill match
- Missing in-demand skills
- Alignment with current tech market trends
- Role suitability

This helps users identify skill gaps and improve employability.

--- 

### 8. Incremental Data Updates

SkillScope supports incremental updates without reprocessing the entire dataset.

The system can:

- Detect newly scraped jobs
- Process only unseen job postings
- Update the database efficiently
- Preserve existing data

This makes the platform scalable and efficient for continuous updates.

----

### 9. REST API Support

SkillScope exposes backend APIs through FastAPI.

Available capabilities include:

- Job search
- Salary statistics
- Trend analysis
- Company insights
- Location analytics
- Tech stack statistics
- Incremental database updates

This enables easy frontend integration and future system expansion.

----

## 🧠 Technical Decisions

### 1. SQLite as Primary Database

SkillScope uses SQLite instead of PostgreSQL or MySQL.

Why SQLite was chosen:
- Lightweight and file-based (no server setup required)
- Ideal for local development and academic projects
- Fast read performance for analytics queries
- Simple integration with Python pipelines

Trade-off:
- ❌ Not suitable for high-concurrency production workloads
- ❌ Limited scaling compared to distributed databases
- ✅ Perfect for single-node analytics and prototyping

---

### AI-Powered Data Processing (Gemini Model)

The system uses an AI model (Gemini) for:

- Job classification (tech vs non-tech)
- Tech stack extraction
- Role normalization

Why AI is used instead of rule-based parsing:
- Job descriptions are unstructured and inconsistent
- Keyword-based filtering is unreliable
- AI improves semantic understanding of job content

Trade-off:
- ❌ Higher latency per batch request
- ❌ API cost and rate limits
- ✅ Much higher accuracy and flexibility

---

## ⚠️ Limitations

### 1. Update Latency (Not Real-Time)

The data update pipeline is not instantaneous.

- Full pipeline execution takes approximately ~2 minutes
- This includes:
  - Job scraping
  - AI-based filtering
  - Job detail extraction
  - Database insertion
  - Tech stack analysis

Impact:
- Users do not see real-time job updates
- API /updates endpoint runs a full or partial pipeline synchronously

Reason:
- AI processing (Gemini API calls) introduces latency
- Batch processing is used to reduce API cost and rate limits
- Web scraping requires controlled delays to avoid blocking

----

### 2. AI Dependency

Several core features rely on external AI models:
- Tech job classification
- Tech stack extraction
- Role normalization

Limitations:
- Dependent on API availability
- Subject to rate limits
- Occasional inconsistent predictions

---

### 3. Web Scraping Fragility

The system scrapes job data from external job boards.

Issues:
- HTML structure changes may break parsers
- Some job listings may be incomplete or inconsistent
- Rate limiting or blocking from source websites may occur

---

### 4. Job Description Fetch Reliability

Some job descriptions fail to load due to:

- Broken or expired job URLs
- Network timeouts
- Missing content on source page

Result:
- Some jobs may have `"description": "Unknown"`

---

### 5. Batch Processing Delay

AI processing is done in batches to optimize performance.

Trade-off:
- Reduces API cost and avoids rate limits
- But introduces processing delay before results are available

---

## 🚀 Future Improvements

### 1. Real-Time or Near Real-Time Updates
- Convert pipeline into async queue-based system (e.g., Celery / Redis Queue)
- Enable background processing for /updates endpoint
- Reduce visible latency from ~2 minutes to near real-time experience

---

### 2. Replace SQLite with Scalable Database
- Migrate to PostgreSQL or MySQL
- Support concurrent writes and larger datasets
- Improve query performance for analytics

---

### 3. Caching Layer
- Add Redis caching for:
  - Trend analytics
  - Salary statistics
  - Frequent API responses
- Reduce repeated database queries

--- 

### 4. Improved AI Pipeline
- Fine-tune model for job-specific classification
- Reduce dependency on external API calls
- Add fallback rule-based system for reliability

---

### 5. More Robust Web Scraping
- Add retry + fallback scraping strategies
- Use headless browser (Playwright / Selenium) for dynamic pages
- Improve resilience against HTML structure changes

---

### 6. Resume Matching Enhancements
- Add ranking score instead of simple matching
- Provide personalized job recommendations
- Improve skill gap analysis with weighted importance