from collections import Counter
from backend.utils.error_handlers import (
    InternalServerError,
    UnprocessableEntityError
)
from backend.core.database.connection import get_db


def fetch_posted_dates(role: str | None = None):
    """Fetch posted dates from jobs table."""
    with get_db() as conn:
        cursor = conn.cursor()

        if role:
            cursor.execute("""
                SELECT actual_posted_date
                FROM jobs
                WHERE role = ?
            """, (role,))
        else:
            cursor.execute("""
                SELECT actual_posted_date
                FROM jobs
            """)

        rows = cursor.fetchall()

        if not rows:
            raise InternalServerError("No job data found")

        return rows


def get_posted_trend(role: str | None = None):
    """Get posting trend (optionally filtered by role)."""
    try:
        if role is not None and not role.strip():
            raise UnprocessableEntityError("Role cannot be empty")

        rows = fetch_posted_dates(role)

        dates = [
            row["actual_posted_date"]
            for row in rows
            if row["actual_posted_date"] is not None
        ]

        date_counts = Counter(dates)

        jobs_list = [
            {"date": date, "count": count}
            for date, count in date_counts.items()
        ]

        # Highest occurrence first
        jobs_list.sort(key=lambda x: x["count"], reverse=True)

        return {
            "message": "Successfully fetched job posting trend",
            "data": {
                "total": len(dates),
                "jobs": jobs_list
            }
        }

    except UnprocessableEntityError:
        raise

    except Exception as e:
        raise InternalServerError(f"Error fetching job trend: {str(e)}")


def get_trend_by_role(role: str):
    return get_posted_trend(role)