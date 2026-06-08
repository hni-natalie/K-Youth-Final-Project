# 📘 Job Market Stats API Documentation

Base URL:

```text
http://localhost:8001/api/stats_by_role
```

These endpoints return statistics filtered by a specific job role.

All endpoints require a query parameter:

```
?role=<role_name>
```

Example:

```
?role=Data Scientist
```

---

## 📍 1. Get Locations by Role

### Endpoint

```
GET /locations?role=<role_name>
```

### Response
```json
{
  "message": "Locations retrieved successfully",
  "data": {
    "locations": [
      {
        "location": "Kuala Lumpur",
        "count": 52
      },
      {
        "location": "Selangor",
        "count": 31
      }
    ]
  }
}
```

---

## 🏢 2. Get Companies by Role

### Endpoint

```
GET /companies?role=<role_name>
```

### Response
```json
{
  "message": "Company statistics retrieved successfully",
  "data": {
    "companies": [
      {
        "company": "Intel",
        "count": 22
      },
      {
        "company": "Accenture",
        "count": 15
      }
    ]
  }
}
```

----

## 💰 3. Get Salary by Role

### Endpoint

```
GET /salary?role=<role_name>
```

### Response
```json
{
  "message": "Salary statistics retrieved successfully",
  "data": {
    "average": 13047.06,
    "median": 7500.0,
    "min": 1500.0,
    "max": 100000.0,
    "undisclosed_count": 34,
    "total_valid_count": 17,
    "total_data_count": 51,
    "distribution": {
      "MYR 3,000–5,000": 4,
      "MYR 5,000–8,000": 5,
      "MYR 8,000–12,000": 5,
      "MYR 12,000+": 3
    }
  }
}
```

----

## 📈 4. Get Trend by Role

### Endpoint

```
GET /trend?role=<role_name>
```

### Response
```json
{
  "message": "Successfully fetched job posting trend",
  "data": {
    "total": 51,
    "jobs": [
      {
        "date": "2026-05-07",
        "count": 6
      },
      {
        "date": "2026-05-28",
        "count": 5
      }
    ]
  }
}
```

----

## 🧠 5. Get Tech Stack by Role

### Endpoint

```
GET /tech?role=<role_name>
```

### Response
```json
{
  "message": "Tech stack statistics retrieved successfully",
  "data": {
    "role": "AI Engineer",
    "top_skills": {
      "python": 21,
      "large language models": 8,
      "artificial intelligence": 7
    }
  }
}
```

----
