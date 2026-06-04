# 📘 Job Market Stats API Documentation

Base URL:

```text
http://localhost:8001/api/stats
```

---

## 📊 1. Get Target Roles

**Endpoint:**  

```text
GET /roles
```

**Description:**  
Returns a distinct list of all standardized job role categories from the database.

**Response:**  
```json
{
  "message": "Roles retrieved successfully",
  "data": {
    "roles": [
      "AI/ML Engineering",
      "Artificial Intelligence",
      "Business Systems Analysis",
      ...
    ]
  }
}
```

---

## 📊 2. Get Roles with Count 

**Endpoint:**  

```text
GET /roles_count
```

**Description:**  
- Returns a list of all standardized tech roles with the number of job postings associated with each role.
- This endpoint is useful for analytics and statistics, e.g., finding which tech roles are most in-demand.

**Response:**  
```json
{
  "message": "Role statistics retrieved successfully",
  "data": {
    "roles": [
      {"role": "AI Engineer", "count": 12},
      {"role": "Software Engineer", "count": 8},
      {"role": "Data Scientist", "count": 5},
      {"role": "DevOps Engineer", "count": 3},
        ...
    ]
  }
}
```

---

## 📊 3. Get Distinct Location 

**Endpoint:**  

```text
GET /location
```

**Description:**  
Returns a distinct list of all job locations from the database. Variations in naming (e.g., "KL City", "WP Kuala Lumpur") are normalized to canonical names (e.g., "Kuala Lumpur").

**Response:**  
```json
{
  "message": "Locations retrieved successfully",
  "data": {
    "locations": [
      "Bandar Tun Razak",
      "Cheras",
      "Cyberjaya",
        ... 
    ]
  }
}
```

---

## 📊 4. Get Location with Count 

**Endpoint:**  

```text
GET /location_count
```

**Description:**  
Returns all job locations along with the number of job postings for each location. The locations are normalized to canonical names and sorted by highest count first.

**Response:**  
```json
{
  "message": "Location statistics retrieved successfully",
  "data": {
    "locations": [
      {"location": "Singapore", "count": 49},
      {"location": "Kuala Lumpur", "count": 42},
      {"location": "Petaling Jaya", "count": 28},
        ...
    ]
  }
}
```

---

## 📊 5. Get Salary Stats 

**Endpoint:**  

```text
GET /salary
```

**Description:**  
Returns aggregated salary statistics from job listings, including:

- Average salary
- Median salary
- Minimum and maximum salary
- Number of undisclosed salaries
- Total valid salary records
- Total dataset size
- Distribution of salary ranges

**Response:**  
```json
{
  "message": "Salary statistics retrieved successfully",
  "data": {
    "average": 6403.57,
    "median": 5500.0,
    "min": 1000,
    "max": 25000,
    "undisclosed_count": 82,
    "total_valid_count": 56,
    "total_data_count": 138,
    "distribution": {
      "MYR 5,000–8,000": 20,
      "MYR 8,000–12,000": 12,
      "MYR 3,000–5,000": 16,
      "MYR 12,000+": 8
    }
  }
}
```

---

## 📊 5. Get Trend Stats 

**Endpoint:**  

```text
GET /trend
```

**Description:**  
Returns trending tech skills extracted from job listings.

#### The system:

- Extracts raw tech_stack values from database
- Splits comma-separated skills
- Uses LLM to:
    - Remove non-tech skills
    - Normalize similar skills (e.g. AI → artificial intelligence)
- Aggregates frequency count of each normalized skill
- Returns ranked “top skills” based on occurrences

**Response:**  
```json
{
  "message": "Tech stack statistics retrieved successfully",
  "data": {
    "top_skills": {
      "python": 55,
      "machine learning": 23,
      "pytorch": 15,
      "sql": 15,
        ... 
    }
  }
}
```

---

## 📊 6. Get Company Stats 

**Endpoint:**  

```text
GET /company
```

**Description:**  
Returns a list of companies extracted from job postings, along with how many job listings each company has.

#### This endpoint helps identify:

- Most active hiring companies
- Job posting concentration
- Company distribution across dataset

**Response:**  
```json
{
  "message": "Company statistics retrieved successfully",
  "data": {
    "companies": [
      {
        "company": "PGH Group Trading Sdn Bhd",
        "count": 11
      },
      {
        "company": "Easytech International Sdn Bhd",
        "count": 6
      },
      {
        "company": "PERSOL Workforce Solutions Malaysia Sdn Bhd",
        "count": 6
      },
      {
        "company": "Compass Beam Capital",
        "count": 5
      },
        ...
    ]
  }
}
```

---

## 📊 7. Get Tech Stack Stats 

**Endpoint:**  

```text
GET /tech_stack
```

**Description:**  
Returns the frequency distribution of technology stacks found in job postings. This endpoint aggregates all `tech_stack` values from the database and counts how often each stack appears, helping identify the most in-demand technologies.

**Response:**  
```json
{
  "message": "Successfully fetched tech stack statistics",
  "data": {
    "total": 138,
    "tech_stack": [
      {
        "stack": "python",
        "count": 45
      },
      {
        "stack": "javascript",
        "count": 30
      },
      {
        "stack": "java",
        "count": 20
      },
      {
        "stack": "go",
        "count": 10
      }
    ]
  }
}
```

---

## 📊 8. Add New Data 

Base URL:

```text
http://localhost:8001/api
```

**Endpoint:**  

```text
GET /updates
```

**Description:**  
This endpoint triggers the full job pipeline, which includes:

- Fetching newly scraped job postings
- Comparing with existing database records to remove duplicates
- Extracting and saving structured job data
- Inserting new jobs into the database
- Running AI enrichment (role classification + tech stack extraction)

It returns the number of newly inserted jobs and total processing time.

**Response:**  
```json
{
  "message": "Pipeline executed successfully",
  "data": {
    "number_of_data_newly_added": 69,
    "time_taken_seconds": 120.03
  }
}
```

---