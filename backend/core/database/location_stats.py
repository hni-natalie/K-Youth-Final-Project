from collections import Counter
from backend.utils.error_handlers import InternalServerError
from backend.core.database.connection import get_db

# Mapping common variations to canonical location names
LOCATION_MAPPING = {
    "Kuala Lumpur": ["wp kuala lumpur", "kl city", "kuala lumpur"],
    "Petaling Jaya": ["petaling jaya", "pj"],
    "Shah Alam": ["shah alam"],
    "Subang Jaya": ["subang jaya"],
    "Puchong": ["puchong"],
    "Gombak": ["gombak"],
    "Skudai": ["skudai"],
    "Senai": ["senai"],
    "Johor Bahru": ["johor bahru", "jb"],
    "Cyberjaya": ["cyberjaya"],
    "Singapore": ["singapore"],
    "Klang": ["klang"],
    "Cheras": ["cheras"],
}


def fetch_locations() -> list[str]:
    """Fetch all locations from DB (including duplicates for counting)."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT location FROM jobs WHERE location IS NOT NULL")
        rows = cursor.fetchall()

        if not rows:
            raise InternalServerError("No locations found in database")

        return [row["location"] for row in rows]


def normalize_location(location: str) -> str:
    """Normalize location to canonical name using mapping."""
    loc_lower = location.lower().strip()
    for canonical, aliases in LOCATION_MAPPING.items():
        for alias in aliases:
            if alias in loc_lower:
                return canonical
    return location.strip()  # fallback to original


def get_locations():
    """Return distinct locations."""
    try:
        locations = fetch_locations()
        normalized = {normalize_location(loc) for loc in locations}
        location_list = sorted(normalized)

        return {
            "message": "Locations retrieved successfully",
            "data": {"locations": location_list},
        }

    except Exception as e:
        raise InternalServerError(f"Failed to fetch locations: {str(e)}")


def get_locations_with_stats():
    """Return locations with number of appearances."""
    try:
        locations = fetch_locations()
        normalized = [normalize_location(loc) for loc in locations]
        counter = Counter(normalized)

        stats_list = sorted(
            [{"location": loc, "count": count} for loc, count in counter.items()],
            key=lambda x: x["count"],
            reverse=True,
        )

        return {
            "message": "Location statistics retrieved successfully",
            "data": {"locations": stats_list},
        }

    except Exception as e:
        raise InternalServerError(f"Failed to fetch location stats: {str(e)}")


def get_locations_by_role(role: str):
    """Return normalized locations with appearance count for a role."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''
                SELECT location
                FROM jobs
                WHERE role = ?
                AND location IS NOT NULL
                ''',
                (role,),
            )

            rows = cursor.fetchall()

        if not rows:
            return {
                "message": "No locations found",
                "data": {"locations": []}
            }

        # normalize locations
        normalized = [
            normalize_location(row["location"])
            for row in rows
            if row["location"]
        ]

        # count frequency
        counter = Counter(normalized)

        # format response
        stats_list = sorted(
            [
                {
                    "location": location,
                    "count": count
                }
                for location, count in counter.items()
            ],
            key=lambda x: x["count"],
            reverse=True
        )

        return {
            "message": "Locations retrieved successfully",
            "data": {
                "locations": stats_list,
                "total_locations": len(counter),
                "total_records": sum(counter.values())
            }
        }

    except Exception as e:
        raise InternalServerError(
            f"Failed to fetch locations by role: {str(e)}"
        )

