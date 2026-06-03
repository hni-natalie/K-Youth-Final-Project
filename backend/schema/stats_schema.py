from pydantic import BaseModel
from typing import Optional

class PipelineSummary(BaseModel):
    stage_1_total: int
    stage_1_saved: int
    stage_2_total: int
    stage_2_saved: int
    stage_2_duplicates: int
    total_jobs_stored: int

class JobTechStats(BaseModel):
    tech_stack: str
    job_count: int
    avg_salary: Optional[str] = None