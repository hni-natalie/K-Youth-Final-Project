import re
from collections import Counter
from statistics import mean, median
from backend.utils.error_handlers import InternalServerError
from backend.core.database.connection import get_db

def fetch_salaries() -> list[str]:
    """Fetch salary column from jobs table."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT salary FROM jobs")
        rows = cursor.fetchall()
        if not rows:
            raise InternalServerError("No salaries found in database")
        return [row["salary"] for row in rows if row["salary"]]


def parse_salary(salary_str: str):
    if not salary_str:
        return None

    if "undisclosed" in salary_str.lower():
        return None

    # remove weird escaping + commas
    cleaned = salary_str.replace("\\", "").replace(",", "")

    # extract full numbers (IMPORTANT FIX)
    nums = re.findall(r"\d+", cleaned)

    print(f"      🔍 cleaned: {cleaned}")
    print(f"      🔢 extracted nums: {nums}")

    if not nums:
        return None

    # convert safely
    numbers = list(map(int, nums))

    # handle range (assume first 2 numbers = min/max)
    if len(numbers) >= 2:
        min_salary = numbers[0]
        max_salary = numbers[1]
    else:
        min_salary = max_salary = numbers[0]

    # sanity fix (swap if wrong)
    if min_salary > max_salary:
        min_salary, max_salary = max_salary, min_salary

    return min_salary, max_salary

def assign_salary_range(min_sal: int, max_sal: int):
    """Map numeric salary to predefined range categories."""
    # You can tweak ranges as needed
    if max_sal < 5000:
        return "MYR 3,000–5,000"
    elif max_sal < 8000:
        return "MYR 5,000–8,000"
    elif max_sal < 12000:
        return "MYR 8,000–12,000"
    else:
        return "MYR 12,000+"


def get_salary_stats():
    try:
        salaries_raw = fetch_salaries()

        parsed_salaries = []
        undisclosed_count = 0

        print("\n📥 RAW SALARIES SAMPLE (first 20):")
        print(salaries_raw[:20])

        for idx, s in enumerate(salaries_raw):
            print(f"\n🔎 Processing [{idx}] -> {s}")

            parsed = parse_salary(s)

            print(f"   🧪 Parsed result: {parsed}")

            if parsed is None:
                undisclosed_count += 1
                print("   ⚠️ Classified as UNDISCLOSED")
            else:
                min_sal, max_sal = parsed

                print(f"   📊 Min: {min_sal}, Max: {max_sal}")

                # 🚨 sanity check (VERY IMPORTANT)
                if min_sal > max_sal:
                    print("   ❌ ERROR: min > max detected!")

                if max_sal > 100000:
                    print("   🚨 WARNING: unusually high salary detected!")

                parsed_salaries.append(parsed)

        print("\n📦 PARSING SUMMARY")
        print(f"Valid salaries: {len(parsed_salaries)}")
        print(f"Undisclosed: {undisclosed_count}")

        # Flatten
        all_numbers = []
        for min_sal, max_sal in parsed_salaries:
            all_numbers.append(min_sal)
            all_numbers.append(max_sal)

        print("\n📊 FLATTENED NUMBERS SAMPLE:")
        print(all_numbers[:20])

        if not all_numbers:
            raise InternalServerError("No valid salary data")

        avg_salary = round(mean(all_numbers), 2)
        median_salary = round(median(all_numbers), 2)
        min_salary = min(all_numbers)
        max_salary = max(all_numbers)

        print("\n📈 FINAL STATS (RAW)")
        print(f"Avg: {avg_salary}")
        print(f"Median: {median_salary}")
        print(f"Min: {min_salary}")
        print(f"Max: {max_salary}")

        # Distribution debug
        range_counter = Counter(
            assign_salary_range(min_sal, max_sal)
            for min_sal, max_sal in parsed_salaries
        )

        print("\n📊 DISTRIBUTION DEBUG:")
        for k, v in range_counter.items():
            print(f"{k}: {v}")

        total_valid = len(parsed_salaries)
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

    except Exception as e:
        print("💥 ERROR OCCURRED:", str(e))
        raise InternalServerError(f"Failed to fetch salary stats: {str(e)}")