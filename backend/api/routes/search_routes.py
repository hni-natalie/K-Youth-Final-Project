# backend/api/routes/stats_routes.py
from fastapi import APIRouter, Query
from backend.core.database.search import (
    get_total_jobs,
    get_jobs_by_tech,
    get_jobs_by_company,
    get_jobs_by_salary,
    get_jobs_by_location,
    get_all_jobs,
    get_jobs_by_role,
)

router = APIRouter()


@router.get("/total-jobs")
def read_total_jobs():
    return get_total_jobs()


@router.get("/all-jobs")
def read_all_jobs():
    return get_all_jobs()


@router.get("/jobs/by-tech/{tech}")
def read_jobs_by_tech(tech: str):
    return get_jobs_by_tech(tech)


@router.get("/jobs/by-company/{company_name}")
def read_jobs_by_company(company_name: str):
    """Get all jobs from a specific company"""
    return get_jobs_by_company(company_name)


@router.get("/jobs/by-salary/{amount}")
def read_jobs_by_salary(amount: float):
    """Get all jobs that include the given salary in their range"""
    return get_jobs_by_salary(amount)


@router.get("/jobs/by-location/{location}")
def read_jobs_by_location(location: str):
    """Get all jobs from a specific location"""
    return get_jobs_by_location(location)

@router.get("/jobs/by-role/{role}")
def read_jobs_by_role(role: str):
    """Get all jobs for a given role (for analyze page)"""
    return get_jobs_by_role(role)