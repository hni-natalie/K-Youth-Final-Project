from fastapi import APIRouter
from backend.core.database.role_stats import get_roles, get_roles_with_stats
from backend.core.database.location_stats import get_locations, get_locations_with_stats
from backend.core.database.salary_stats import get_salary_stats
from backend.core.database.company_stats import get_company_stats
from backend.core.database.tech_stack_stats import get_tech_stack_stats
from backend.core.database.trend_stats import get_posted_trend

router = APIRouter()

@router.get("/roles")
def read_roles():
    return get_roles()

@router.get("/roles_count")
def read_roles_count():
    return get_roles_with_stats()

@router.get("/locations")
def read_locations():
    return get_locations()

@router.get("/locations_count")
def read_locations_count():
    return get_locations_with_stats()

@router.get("/salary")
def read_salary_stats():
    return get_salary_stats()

@router.get("/company")
def read_company_stats():
    return get_company_stats()

@router.get("/tech_stack")
def read_tech_stack_stats():
    return get_tech_stack_stats()

@router.get("/trend")
def read_trend_stats():
    return get_posted_trend()
