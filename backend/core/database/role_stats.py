from backend.utils.error_handlers import InternalServerError
from backend.core.database.connection import get_db


def get_roles():
    """Return distinct roles from database."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT DISTINCT role
                FROM jobs
                WHERE role IS NOT NULL
                  AND role != ''
                ORDER BY role ASC
            """)

            rows = cursor.fetchall()

            roles_list = [row["role"] for row in rows]

        return {
            "message": "Roles retrieved successfully",
            "data": {
                "roles": roles_list
            }
        }

    except Exception as e:
        print("💥 ERROR OCCURRED:", str(e))
        raise InternalServerError(
            f"Failed to fetch roles: {str(e)}"
        )


def get_roles_with_stats():
    """Return roles with number of appearances."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT role, COUNT(*) AS count
                FROM jobs
                WHERE role IS NOT NULL
                  AND role != ''
                GROUP BY role
                ORDER BY count DESC
            """)

            rows = cursor.fetchall()

            stats_list = [
                {
                    "role": row["role"],
                    "count": row["count"]
                }
                for row in rows
            ]

        return {
            "message": "Role statistics retrieved successfully",
            "data": {
                "roles": stats_list
            }
        }

    except Exception as e:
        print("💥 ERROR OCCURRED:", str(e))
        raise InternalServerError(
            f"Failed to fetch role stats: {str(e)}"
        )