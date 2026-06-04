from collections import Counter
from backend.utils.error_handlers import InternalServerError
from backend.core.database.connection import get_db


def get_posted_trend():
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT actual_posted_date FROM jobs")
            rows = cursor.fetchall()

        # extract dates
        dates = [row[0] for row in rows if row[0] is not None]

        # count occurrences
        date_counts = Counter(dates)

        # build response list
        jobs_list = [
            {"date": date, "count": count}
            for date, count in date_counts.items()
        ]

        # sort by date (important for trend visualization)
        jobs_list.sort(key=lambda x: x["date"])

        return {
            "message": "Successfully fetched job posting trend",
            "data": {
                "total": len(dates),
                "jobs": jobs_list
            }
        }

    except Exception as e:
        raise InternalServerError(f"Error fetching job trend: {str(e)}")