from backend.utils.error_handlers import InternalServerError
from backend.core.database.connection import get_db

def get_total_jobs():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM jobs")
            result = cursor.fetchone()
            if result is None:
                raise InternalServerError("No data returned from database")

            return {
                "message": "Total jobs retrieved",
                "data": {"total_jobs": result["count"]}
            }

    except Exception as e:
        raise InternalServerError(f"Unexpected error: {str(e)}")

def get_all_jobs():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT title, company, location, salary, tech_stack, actual_posted_date, job_url
                FROM jobs
            ''')

            jobs = cursor.fetchall()
            job_list = [dict(job) for job in jobs]

            return {
                "message": f"Found {len(job_list)} jobs",
                "data": {"total": len(job_list), "jobs": job_list}
            }

    except Exception as e:
        raise InternalServerError(f"Error searching jobs by tech: {str(e)}")


def get_jobs_by_tech(tech: str):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT title, company, location, salary, tech_stack, actual_posted_date, job_url
                FROM jobs
                WHERE LOWER(tech_stack) LIKE LOWER(?)
            ''', (f"%{tech}%",))

            jobs = cursor.fetchall()
            job_list = [dict(job) for job in jobs]

            return {
                "message": f"Found {len(job_list)} jobs",
                "data": {"total": len(job_list), "jobs": job_list}
            }

    except Exception as e:
        raise InternalServerError(f"Error searching jobs by tech: {str(e)}")


def get_jobs_by_company(company_name: str):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT title, company, location, salary, tech_stack, actual_posted_date, job_url
                FROM jobs
                WHERE LOWER(company) LIKE LOWER(?)
            ''', (f"%{company_name}%",))

            jobs = cursor.fetchall()
            job_list = [dict(job) for job in jobs]

            return {
                "message": f"Found {len(job_list)} jobs",
                "data": {"total": len(job_list), "jobs": job_list}
            }

    except Exception as e:
        raise InternalServerError(f"Error searching jobs by company: {str(e)}")
    

def get_jobs_by_location(location: str):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT title, company, location, salary, tech_stack, actual_posted_date, job_url
                FROM jobs
                WHERE LOWER(location) LIKE LOWER(?)
            ''', (f"%{location}%",))

            jobs = cursor.fetchall()
            job_list = [dict(job) for job in jobs]

            return {
                "message": f"Found {len(job_list)} jobs",
                "data": {"total": len(job_list), "jobs": job_list}
            }

    except Exception as e:
        raise InternalServerError(f"Error searching jobs by location: {str(e)}")


def get_jobs_by_salary(input_salary: float):
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT title, company, location, salary, tech_stack, actual_posted_date, job_url
                FROM jobs
                WHERE salary != "undisclosed" AND salary IS NOT NULL
            ''')

            all_jobs = cursor.fetchall()
            matching_jobs = []

            for job in all_jobs:
                job_dict = dict(job)
                salary_str = job_dict["salary"]

                try:
                    cleaned = salary_str.replace("MYR", "").replace(",", "").replace(" ", "")
                    if "-" in cleaned:
                        min_str, max_str = cleaned.split("-")
                        min_sal = float(min_str)
                        max_sal = float(max_str)

                        if min_sal <= input_salary <= max_sal:
                            matching_jobs.append(job_dict)
                except Exception:
                    continue  # skip undisclosed salary

            return {
                "message": f"Found {len(matching_jobs)} jobs",
                "data": {"total": len(matching_jobs), "jobs": matching_jobs}
            }
        
    except Exception as e:
        raise InternalServerError(f"Error searching jobs by salary: {str(e)}")


def get_jobs_by_role(role: str):
    """Return all jobs for a given role (used for analyze page)."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT title, company, location, salary, tech_stack,
                       actual_posted_date, job_url
                FROM jobs
                WHERE role = ?
                """,
                (role,),
            )
            jobs = cursor.fetchall()
            job_list = [dict(job) for job in jobs]
        return {
            "message": f"Found {len(job_list)} jobs",
            "data": {"total": len(job_list), "jobs": job_list},
        }
    except Exception as e:
        raise InternalServerError(f"Error fetching jobs by role: {str(e)}")
