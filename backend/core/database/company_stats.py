from collections import Counter
from backend.utils.error_handlers import InternalServerError
from backend.core.database.connection import get_db


def fetch_companies() -> list[str]:
    """Fetch company names from DB."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT company FROM jobs")
        rows = cursor.fetchall()

        if not rows:
            raise InternalServerError("No company data found")

        return [row["company"] for row in rows if row["company"]]


def normalize_company_key(name: str) -> str:
    """Normalize company name for counting (case-insensitive)."""
    if not name:
        return None
    name = name.strip()
    name = " ".join(name.split())
    return name.lower()


def format_company_name(name: str) -> str:
    """Format company name for display."""
    if not name:
        return None

    def smart_title(word: str) -> str:
        # Keep all-uppercase acronyms as-is (e.g., IIUM, KWSP)
        if word.isupper():
            return word
        return word.capitalize()

    return " ".join(smart_title(w) for w in name.split())


def get_company_stats():
    """Return company frequency statistics."""
    try:
        companies_raw = fetch_companies()

        counter = Counter()

        print("\n📊 Processing company data...")

        for c in companies_raw:
            key = normalize_company_key(c)
            if not key:
                continue
            counter[key] += 1

        # Prepare output with nicely formatted names
        stats = [
            {
                "company": format_company_name(name),
                "count": count
            }
            for name, count in counter.most_common()
        ]

        return {
            "message": "Company statistics retrieved successfully",
            "data": {
                "companies": stats,
                "total_unique": len(counter),
                "total_records": sum(counter.values())
            }
        }

    except Exception as e:
        print("💥 ERROR:", str(e))
        raise InternalServerError(f"Failed to fetch company stats: {str(e)}")


def get_companies_by_role(role: str) -> dict:
    """
    Get company frequency filtered by job title (role keyword match).
    Example: 'data scientist', 'software engineer'
    """

    if not role:
        raise InternalServerError("Role cannot be empty")

    try:
        with get_db() as conn:
            cursor = conn.cursor()

            query = """
                SELECT company
                FROM jobs
                WHERE LOWER(role) LIKE ?
            """

            cursor.execute(query, (f"%{role.lower()}%",))
            rows = cursor.fetchall()

            if not rows:
                raise InternalServerError(f"No jobs found for role: {role}")

            counter = Counter()

            for row in rows:
                company = row["company"]
                if not company:
                    continue

                key = normalize_company_key(company)
                counter[key] += 1

            stats = [
                {
                    "company": format_company_name(name),
                    "count": count
                }
                for name, count in counter.most_common()
            ]

            return {
                "message": f"Company stats for role: {role}",
                "data": {
                    "companies": stats,
                    "total_unique": len(counter),
                    "total_records": sum(counter.values())
                }
            }

    except Exception as e:
        print("💥 ERROR:", str(e))
        raise InternalServerError(f"Failed to fetch companies by role: {str(e)}")