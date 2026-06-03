# 📘 Job Market API Documentation

Base URL:

```text
http://localhost:8001/api/search
```

---

## 📊 1. Get Total Jobs

**Endpoint:**  

```text
GET /total-jobs
```

**Description:**  
Returns the total number of jobs in the database.

**Response:**  
```json
{
  "message": "Total jobs retrieved",
  "data": {
    "total_jobs": 128
  }
}
```

---

## 📊 2. Get All Jobs

**Endpoint:**  

```text
GET /all-jobs
```

**Description:**  
Returns all jobs in the database.

**Response:**  
```json
{
  "message": "Found 138 jobs",
  "data": {
    "total": 138,
    "jobs": [
      {
        "title": "Backend Developer",
        "company": "ABC Tech",
        "location": "Kuala Lumpur",
        "salary": "MYR 4000 - 6000",
        "tech_stack": "Python, FastAPI",
        "job_url": "https://..."
      }
    ]
  }
}
```

---


## 🧠 3. Get Jobs by Technology

**Endpoint:**  

```text
GET /jobs/by-tech/{tech}
```

**Description:**  
Search jobs by tech stack (partial match supported).

**Path Parameter:**
| Parameter | Type   | Description                                   |
| --------- | ------ | --------------------------------------------- |
| tech      | string | Technology keyword (e.g. python, react, java) |


**Response:**  
```json
{
  "message": "Found 12 jobs",
  "data": {
    "total": 12,
    "jobs": [
      {
        "title": "Backend Developer",
        "company": "ABC Tech",
        "location": "Kuala Lumpur",
        "salary": "MYR 4000 - 6000",
        "tech_stack": "Python, FastAPI",
        "job_url": "https://..."
      }
    ]
  }
}
```

---

## 🏢 4. Get Jobs by Company

**Endpoint:**  

```text
GET /jobs/by-company/{company_name}
```

**Description:**  
Returns jobs posted by a specific company (partial match supported).

**Path Parameter:**
| Parameter    | Type   | Description                    |
| ------------ | ------ | ------------------------------ |
| company_name | string | Company name (full or partial) |


**Response:**  
```json
{
  "message": "Found 5 jobs",
  "data": {
    "total": 5,
    "jobs": [
      {
        "title": "Software Engineer",
        "company": "ABC",
        "location": "KL City",
        "salary": "MYR 8000 - 12000",
        "tech_stack": "Go, Python",
        "posted_date": "2026-06-01",
        "job_url": "https://..."
      }
    ]
  }
}
```

---

## 📍 5. Get Jobs by Location

**Endpoint:**  

```text
GET /jobs/by-location/{location}
```

**Description:**  
Search jobs by location (partial match supported).

**Path Parameter:**
| Parameter | Type   | Description                              |
| --------- | ------ | ---------------------------------------- |
| location  | string | Job location (e.g. Kuala Lumpur, Remote) |

**Response:**  
```json
{
  "message": "Found 5 jobs",
  "data": {
    "total": 5,
    "jobs": [
      {
        "title": "Software Engineer",
        "company": "Google",
        "location": "Remote",
        "salary": "MYR 8000 - 12000",
        "tech_stack": "Go, Python",
        "posted_date": "2026-06-01",
        "job_url": "https://..."
      }
    ]
  }
}
```

---

## 💰 6. Get Jobs by Salary Range

**Endpoint:**  

```text
GET /jobs/by-salary/{amount}
```

**Description:**  
Returns jobs whose salary range includes the given value.

**Path Parameter:**
| Parameter | Type  | Description                       |
| --------- | ----- | --------------------------------- |
| amount    | float | Salary value to match (e.g. 5000) |

**Response:**  
```json
{
  "message": "Found 8 jobs",
  "data": {
    "total": 8,
    "jobs": [
      {
        "title": "Data Analyst",
        "company": "ABC Corp",
        "location": "Remote",
        "salary": "MYR 4000 - 6000",
        "tech_stack": "SQL, Python",
        "job_url": "https://..."
      }
    ]
  }
}
```

---

## ⚠️ Error Response Format

**Endpoint:**  
All endpoints follow this error format:

**Response:**  
```json
{
  "message": "Error message",
  "data": null
}
```

### Notes for Frontend
All endpoints return a consistent structure:
```json
{
  "message": "...",
  "data": {
    "total": number,
    "jobs": []
  }
}
```