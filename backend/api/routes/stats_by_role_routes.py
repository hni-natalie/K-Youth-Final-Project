from fastapi import APIRouter
from fastapi import HTTPException
from backend.core.database.location_stats import get_locations_by_role
from backend.core.database.salary_stats import get_salary_by_role
from backend.core.database.company_stats import get_companies_by_role
from backend.core.database.tech_stack_stats import get_tech_stack_stats
from backend.core.database.trend_stats import get_trend_by_role
from backend.utils.error_handlers import InternalServerError, UnprocessableEntityError

router = APIRouter()


@router.get("/locations")
def locations(role: str):
    try:
        return get_locations_by_role(role)
    except UnprocessableEntityError as e:
        raise HTTPException(status_code=422, detail=e.detail)
    except InternalServerError as e:
        raise HTTPException(status_code=500, detail=e.detail)

@router.get("/companies")
def read_companies_by_role(role: str):
    try:
        return get_companies_by_role(role)
    except UnprocessableEntityError as e:
        raise HTTPException(status_code=422, detail=e.detail)
    except InternalServerError as e:
        raise HTTPException(status_code=500, detail=e.detail)
    
@router.get("/salary")
def read_salaries_by_role(role: str):
    try:
        return get_salary_by_role(role)
    except UnprocessableEntityError as e:
        raise HTTPException(status_code=422, detail=e.detail)
    except InternalServerError as e:
        raise HTTPException(status_code=500, detail=e.detail)

@router.get("/tech")
def read_tech_by_role(role: str):
    try:
        return get_tech_stack_stats(role)
    except UnprocessableEntityError as e:
        raise HTTPException(status_code=422, detail=e.detail)
    except InternalServerError as e:
        raise HTTPException(status_code=500, detail=e.detail)
    
@router.get("/trend")
def read_trend_by_role(role: str):
    try:
        return get_trend_by_role(role)
    except UnprocessableEntityError as e:
        raise HTTPException(status_code=422, detail=e.detail)
    except InternalServerError as e:
        raise HTTPException(status_code=500, detail=e.detail)