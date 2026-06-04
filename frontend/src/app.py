import asyncio
import io
import json
import os
import pathlib
import re
from collections import Counter
from typing import Annotated

import httpx
import pypdf
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, Request, Response, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

load_dotenv()

app = FastAPI()

BASE_DIR = pathlib.Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001")
MAX_PDF_BYTES = 10 * 1024 * 1024  # 10 MB


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/static/services/api.js")
async def serve_api_js():
    """Serve the API service module without requiring aiofiles."""
    path = BASE_DIR / "static" / "services" / "api.js"
    content = path.read_text(encoding="utf-8")
    return Response(content=content, media_type="application/javascript")


@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    return templates.TemplateResponse("stats.html", {"request": request})


@app.get("/api/stats")
async def api_stats():
    """Aggregate stats from multiple backend endpoints into one response for the dashboard."""

    def _safe_get(resp, *path, default):
        """Return nested data from an httpx response; return default on any error or non-200."""
        try:
            if isinstance(resp, Exception) or resp.status_code != 200:
                return default
            data = resp.json()
            for key in path:
                data = data[key]
            return data
        except Exception:
            return default

    try:
        def _get_locations():
            return httpx.get(f"{BACKEND_URL}/api/stats/locations_count", timeout=10.0)
        def _get_roles():
            return httpx.get(f"{BACKEND_URL}/api/stats/roles_count", timeout=30.0)
        def _get_jobs():
            return httpx.get(f"{BACKEND_URL}/api/search/all-jobs", timeout=10.0)
        def _get_companies():
            return httpx.get(f"{BACKEND_URL}/api/stats/company", timeout=10.0)

        # return_exceptions=True: a timeout in one endpoint won't cancel the others
        loc_resp, roles_resp, jobs_resp, comp_resp = await asyncio.gather(
            asyncio.to_thread(_get_locations),
            asyncio.to_thread(_get_roles),
            asyncio.to_thread(_get_jobs),
            asyncio.to_thread(_get_companies),
            return_exceptions=True,
        )

        locations_list = _safe_get(loc_resp,   "data", "locations",   default=[])
        roles_list     = _safe_get(roles_resp, "data", "roles",       default=[])
        raw_jobs       = _safe_get(jobs_resp,  "data", "jobs",        default=[])
        companies_list = _safe_get(comp_resp,  "data", "companies",   default=[])

        # Transform each job: split comma-separated tech_stack string into a skills array
        # and simultaneously count skill frequencies for the top_skills chart
        jobs = []
        skill_counter: Counter = Counter()
        for job in raw_jobs:
            j = dict(job)
            tech_stack_str = j.pop("tech_stack", "") or ""
            skills = [s.strip() for s in tech_stack_str.split(",") if s.strip() and s.strip().lower() != "none"]
            j["skills"] = skills
            for s in skills:
                skill_counter[s.lower()] += 1
            jobs.append(j)

        top_skills = dict(skill_counter.most_common())

        # Company stats are already sorted by count desc; take top 10 for the chart
        top_companies = companies_list[:10]

        return JSONResponse({
            "top_skills": top_skills,
            "location_distribution": {item["location"]: item["count"] for item in locations_list},
            "company_distribution": {item["company"]: item["count"] for item in top_companies},
            "total_companies": len(companies_list),
            "job_type_distribution": {item["role"]: item["count"] for item in roles_list},
            "jobs": jobs,
        })
    except Exception as exc:
        return JSONResponse({"error": f"Backend is not available. ({type(exc).__name__}: {exc})"}, status_code=503)


@app.get("/api/roles")
async def api_roles():
    """Return AI-classified role categories from roles_count; falls back to raw DB titles, then preset list."""
    # 1. Try AI-classified roles (pretty grouped names, ~20-35s)
    try:
        def _get_classified():
            return httpx.get(f"{BACKEND_URL}/api/stats/roles_count", timeout=90.0)
        resp = await asyncio.to_thread(_get_classified)
        if resp.status_code == 200:
            roles_data = resp.json().get("data", {}).get("roles", [])
            roles = [r["role"] for r in roles_data if r.get("role")]
            if roles:
                return JSONResponse({"roles": roles})
    except Exception:
        pass
    # 2. Fallback: raw distinct titles from DB (no AI, instant)
    try:
        def _get_raw():
            return httpx.get(f"{BACKEND_URL}/api/search/all-jobs", timeout=15.0)
        resp = await asyncio.to_thread(_get_raw)
        if resp.status_code == 200:
            jobs = resp.json().get("data", {}).get("jobs", [])
            roles = sorted({j["title"] for j in jobs if j.get("title")})
            if roles:
                return JSONResponse({"roles": roles, "_fallback": "raw_titles"})
    except Exception:
        pass
    # 3. Last resort: hardcoded mock roles
    return JSONResponse({"roles": _MOCK_ROLES, "_fallback": "mock"})


@app.get("/api/updates")
async def api_updates():
    """Proxy to backend /api/updates — runs the incremental pipeline (~2 min)."""
    try:
        def _run():
            return httpx.get(f"{BACKEND_URL}/api/updates", timeout=300.0)  # 5 min max
        resp = await asyncio.to_thread(_run)
        return JSONResponse(resp.json(), status_code=resp.status_code)
    except Exception as exc:
        return JSONResponse(
            {"error": f"Update failed: {type(exc).__name__}: {exc}"},
            status_code=503,
        )


@app.get("/api/locations")
async def api_locations(role: str | None = None):
    """Return locations, optionally filtered to only those with jobs for the given role."""
    try:
        if role:
            def _get():
                return httpx.get(
                    f"{BACKEND_URL}/api/stats/locations_by_role",
                    params={"role": role},
                    timeout=10.0,
                )
        else:
            def _get():
                return httpx.get(f"{BACKEND_URL}/api/stats/locations", timeout=5.0)
        resp = await asyncio.to_thread(_get)
        if resp.status_code == 200:
            locations = resp.json().get("data", {}).get("locations", [])
            return JSONResponse({"locations": locations})
    except Exception:
        pass
    return JSONResponse({"locations": _MOCK_LOCATIONS, "_fallback": True})


def _extract_pdf_text(contents: bytes) -> str:
    reader = pypdf.PdfReader(io.BytesIO(contents))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


# ── Analyze endpoint ─────────────────────────────────────────────────────────

_MOCK_TOP_SKILLS: list[dict] = [
    {"skill": "Python", "count": 120},
    {"skill": "SQL", "count": 95},
    {"skill": "Docker", "count": 88},
    {"skill": "Machine Learning", "count": 82},
    {"skill": "Git", "count": 110},
    {"skill": "TensorFlow", "count": 65},
    {"skill": "FastAPI", "count": 60},
    {"skill": "Kubernetes", "count": 55},
    {"skill": "REST API", "count": 70},
    {"skill": "LLM / GenAI", "count": 45},
]

_MOCK_ROLES: list[str] = [
    "AI Engineer",
    "Applied AI Engineer",
    "AI Chatbot Developer",
    "AI Software Engineer",
    "Machine Learning Engineer",
    "Computer Vision Engineer",
    "Data Scientist",
    "Data Engineer",
    "Backend Developer",
    "Full Stack Developer",
    "Software Engineer",
    "DevOps / Cloud Engineer",
    "Algorithm Engineer",
]

_MOCK_LOCATIONS: list[str] = [
    "Kuala Lumpur",
    "Selangor",
    "Cyberjaya, Selangor",
    "Petaling Jaya, Selangor",
    "Penang",
    "Johor Bahru",
    "Melaka",
    "Remote / Malaysia",
]



def _build_analyze_prompt(
    target_role: str,
    location: str,
    user_skills: list[str],
    matched_skills: list[str],
    missing_skills: list[dict],
    match_score: int,
    total_jobs: int,
    expected_salary: str = "",
    pdf_text: str = "",
) -> str:
    skills_str   = ", ".join(user_skills)    if user_skills    else "not specified"
    matched_str  = ", ".join(matched_skills) if matched_skills else "none"
    missing_str  = ", ".join(s["skill"] for s in missing_skills[:5]) if missing_skills else "none"
    resume_part  = f"\nResume excerpt:\n{pdf_text[:600]}" if pdf_text else ""
    salary_part  = f"\nExpected Salary: {expected_salary}"    if expected_salary else ""
    return (
        "You are a career analyst for tech jobs in Malaysia. "
        "Based on the data below, provide specific career advice. "
        "Return ONLY valid JSON with NO markdown.\n\n"
        f"Target Role: {target_role}\n"
        f"Location: {location or 'No preference'}\n"
        f"User Skills: {skills_str}{resume_part}{salary_part}\n"
        f"Match Score: {match_score}% ({total_jobs} job postings analyzed)\n"
        f"Matched Skills: {matched_str}\n"
        f"Top Missing Skills: {missing_str}\n\n"
        "Return exactly this JSON (nothing else):\n"
        '{"ai_recommendation": "<2-3 sentences of specific actionable career advice>", '
        '"limitations": "<1-2 sentences about what this analysis doesn\'t cover>"}'
    )


def _parse_ai_json(reply: str) -> dict:
    clean = re.sub(r"```(?:json)?", "", reply).strip().strip("`")
    match = re.search(r"\{.*\}", clean, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return {}


def _compute_role_skills_analysis(
    user_skills: list[str], top_role_skills: list[dict], pdf_text: str = ""
) -> tuple[list[str], list[dict]]:
    """Returns (matched_skills, missing_skills) based on role tech_stack from DB.
    Checks both the manually entered skills list and the full PDF resume text."""
    user_lower = {s.lower() for s in user_skills}
    pdf_lower = pdf_text.lower() if pdf_text else ""
    matched: list[str] = []
    missing: list[dict] = []
    for i, item in enumerate(top_role_skills):
        skill_name = item["skill"]
        skill_lower = skill_name.lower()
        in_skills_box = skill_lower in user_lower
        in_pdf = bool(pdf_lower) and skill_lower in pdf_lower
        if in_skills_box or in_pdf:
            matched.append(skill_name)
        else:
            priority = "high" if i < 3 else ("medium" if i < 7 else "low")
            missing.append({"skill": skill_name, "priority": priority})
    return matched, missing


_LOCATION_ALIASES: dict[str, list[str]] = {
    "Kuala Lumpur": ["wp kuala lumpur", "kl city", "kuala lumpur"],
    "Petaling Jaya": ["petaling jaya", "pj"],
    "Shah Alam": ["shah alam"],
    "Subang Jaya": ["subang jaya"],
    "Puchong": ["puchong"],
    "Gombak": ["gombak"],
    "Skudai": ["skudai"],
    "Senai": ["senai"],
    "Johor Bahru": ["johor bahru", "jb"],
    "Cyberjaya": ["cyberjaya"],
    "Singapore": ["singapore"],
    "Klang": ["klang"],
    "Cheras": ["cheras"],
}

def _normalize_job_location(raw: str) -> str:
    """Normalize a raw DB location string to its canonical dropdown name."""
    lower = raw.lower().strip()
    for canonical, aliases in _LOCATION_ALIASES.items():
        if any(alias in lower for alias in aliases):
            return canonical
    return raw.strip()


def _filter_jobs_by_location_salary(
    jobs: list[dict], location: str, salary_pref: str
) -> list[dict]:
    """Filter a list of job dicts by location and salary preference."""
    result = jobs
    # Location filter — normalize job location before comparing
    if location and location.lower() != "no preference":
        result = [
            j for j in result
            if _normalize_job_location(j.get("location") or "") == location
        ]
    # Salary filter — extract numeric bounds and compare
    if salary_pref and salary_pref.lower() != "no preference":
        nums = [int(n.replace(",", "")) for n in re.findall(r"\d[\d,]+", salary_pref)]
        if nums:
            pref_min = min(nums)
            pref_max = max(nums) if len(nums) > 1 else None
            filtered = []
            for j in result:
                job_sal = (j.get("salary") or "").replace(",", "")
                job_nums = [int(n) for n in re.findall(r"\d+", job_sal) if int(n) > 500]
                if not job_nums:           # undisclosed — include
                    filtered.append(j)
                    continue
                job_max = max(job_nums)
                job_min = min(job_nums)
                if job_max >= pref_min and (pref_max is None or job_min <= pref_max):
                    filtered.append(j)
            result = filtered
    return result


@app.post("/analyze")
async def analyze(
    target_role: Annotated[str, Form()],
    location: Annotated[str, Form()],
    current_skills: Annotated[str, Form()] = "",
    expected_salary: Annotated[str, Form()] = "",
    pdf: Annotated[UploadFile | None, File()] = None,
):
    # 1. Extract PDF text
    pdf_text = ""
    if pdf and pdf.filename:
        contents = await pdf.read()
        if len(contents) > MAX_PDF_BYTES:
            return JSONResponse({"error": "PDF too large (max 10 MB)."}, status_code=413)
        try:
            pdf_text = _extract_pdf_text(contents)
        except Exception as exc:
            return JSONResponse(
                {"error": f"Could not read PDF ({type(exc).__name__}). "
                           "Please ensure it is a valid PDF file."},
                status_code=400,
            )

    # 2. Parse user skills
    user_skills = [s.strip() for s in current_skills.split(",") if s.strip()]

    # 3. Fetch ALL jobs for this role from backend
    raw_jobs: list[dict] = []
    try:
        def _get_role_jobs():
            return httpx.get(
                f"{BACKEND_URL}/api/search/jobs/by-role",
                params={"role": target_role},
                timeout=15.0,
            )
        jobs_resp = await asyncio.to_thread(_get_role_jobs)
        if jobs_resp.status_code == 200:
            raw_jobs = jobs_resp.json().get("data", {}).get("jobs", [])
    except Exception:
        pass

    # 4. Total jobs for this role (before any filtering)
    total_jobs = len(raw_jobs)

    # 5. Compute top role skills from the fetched jobs (no AI needed)
    from collections import Counter as _Counter
    skill_counter: _Counter = _Counter()
    for job in raw_jobs:
        for skill in (job.get("tech_stack") or "").split(","):
            skill = skill.strip()
            if skill:
                skill_counter[skill] += 1
    top_role_skills: list[dict] = [
        {"skill": k, "count": v} for k, v in skill_counter.most_common(15)
    ]
    if not top_role_skills:
        top_role_skills = _MOCK_TOP_SKILLS

    # 6. Compute matched / missing skills from DB role data (text box + PDF)
    matched_skills, missing_skills = _compute_role_skills_analysis(user_skills, top_role_skills, pdf_text)

    # 7. Match score = matched / (matched + missing) * 100
    total_skill_count = len(matched_skills) + len(missing_skills)
    match_score = round(len(matched_skills) / total_skill_count * 100) if total_skill_count else 0

    # 8. Filter job listings by location + salary for the listings section
    job_listings = _filter_jobs_by_location_salary(raw_jobs, location, expected_salary)

    # 9. Ask AI only for recommendation text (skills + score already computed from DB)
    ai_recommendation = ""
    limitations = "Analysis based on available job listings in the database."
    try:
        prompt = _build_analyze_prompt(
            target_role, location, user_skills, matched_skills, missing_skills,
            match_score, total_jobs, expected_salary, pdf_text,
        )
        def _post_chat():
            return httpx.post(
                f"{BACKEND_URL}/analyze",
                json={"message": prompt, "pdf_text": ""},
                timeout=120.0,
            )
        chat_resp = await asyncio.to_thread(_post_chat)
        if chat_resp.status_code == 200:
            ai_json = _parse_ai_json(chat_resp.json().get("reply", ""))
            ai_recommendation = ai_json.get("ai_recommendation", "")
            limitations = ai_json.get("limitations", limitations)
    except Exception:
        pass

    if not ai_recommendation:
        ai_recommendation = (
            "AI recommendation unavailable — please retry in a moment."
        )

    return JSONResponse({
        "match_score":      match_score,
        "total_jobs":       total_jobs,
        "top_market_skills": top_role_skills[:10],
        "matched_skills":   matched_skills,
        "missing_skills":   missing_skills,
        "ai_recommendation": ai_recommendation,
        "limitations":      limitations,
        "job_listings":     job_listings,
        "expected_salary":  expected_salary or None,
        "_mock":            not bool(raw_jobs),
    })

