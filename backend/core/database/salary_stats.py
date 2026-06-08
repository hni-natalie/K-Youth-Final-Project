from collections import Counter
from statistics import mean, median
from backend.utils.error_handlers import (
    InternalServerError,
    UnprocessableEntityError
)
from backend.core.database.connection import get_db


def fetch_salaries(role: str | None = None):
    """Fetch salary fields from jobs table."""
    with get_db() as conn:
        cursor = conn.cursor()

        if role:
            cursor.execute("""
                SELECT salary_min, salary_max, salary_mean
                FROM jobs
                WHERE role = ?
            """, (role,))
        else:
            cursor.execute("""
                SELECT salary_min, salary_max, salary_mean
                FROM jobs
            """)

        rows = cursor.fetchall()

        if not rows:
            raise InternalServerError("No salaries found in database")

        return rows


def assign_salary_range(max_sal: float):
    """Map salary into salary buckets."""
    if max_sal < 5000:
        return "MYR 3,000–5,000"
    elif max_sal < 8000:
        return "MYR 5,000–8,000"
    elif max_sal < 12000:
        return "MYR 8,000–12,000"
    return "MYR 12,000+"


def get_salary_stats(role: str | None = None):
    """Get salary statistics (optionally filtered by role)."""
    try:
        if role is not None and not role.strip():
            raise UnprocessableEntityError("Role cannot be empty")

        salary_rows = fetch_salaries(role)

        valid_salaries = []
        undisclosed_count = 0

        for idx, row in enumerate(salary_rows):
            min_sal = row["salary_min"]
            max_sal = row["salary_max"]
            mean_sal = row["salary_mean"]

            if min_sal is None or max_sal is None:
                undisclosed_count += 1
                continue

            valid_salaries.append((min_sal, max_sal, mean_sal))

        if not valid_salaries:
            raise InternalServerError("No valid salary data")

        mean_values = [s[2] for s in valid_salaries]

        avg_salary = round(mean(mean_values), 2)
        median_salary = round(median(mean_values), 2)

        min_salary = min(s[0] for s in valid_salaries)
        max_salary = max(s[1] for s in valid_salaries)

        range_counter = Counter(
            assign_salary_range(max_sal)
            for _, max_sal, _ in valid_salaries
        )

        total_valid = len(valid_salaries)
        total_data = total_valid + undisclosed_count

        return {
            "message": "Salary statistics retrieved successfully",
            "data": {
                "average": avg_salary,
                "median": median_salary,
                "min": min_salary,
                "max": max_salary,
                "undisclosed_count": undisclosed_count,
                "total_valid_count": total_valid,
                "total_data_count": total_data,
                "distribution": dict(range_counter)
            }
        }

    except UnprocessableEntityError:
        raise

    except Exception as e:
        print("💥 ERROR OCCURRED:", str(e))
        raise InternalServerError(f"Failed to fetch salary stats: {str(e)}")


def get_salary_by_role(role: str):
    return get_salary_stats(role)