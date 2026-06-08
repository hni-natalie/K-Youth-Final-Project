# 📘 Job Market Updates API Documentation

## Base URL

```text
http://localhost:8001/api/updates
```

---

# 1. Start Pipeline Update

### Endpoint

```http
GET /
```

### Description

Starts the job market data update pipeline in the background.

This endpoint will:

* Fetch newly scraped jobs
* Compare against existing database records
* Add new job data
* Insert normalized job details and tech stack information

The pipeline runs asynchronously in the background, so the response is returned immediately.

### Response Example

```json
{
  "message": "Pipeline started in background",
  "data": {
    "status": "running"
  }
}
```

### Response Fields

| Field         | Type   | Description                                              |
| ------------- | ------ | -------------------------------------------------------- |
| `message`     | string | Status message indicating pipeline execution has started |
| `data.status` | string | Current pipeline status (`running`)                      |

---

# 2. Get Pipeline Status

### Endpoint

```http
GET /status
```

### Description

Returns the current execution status of the update pipeline.

Use this endpoint to check:

* Whether the pipeline is still running
* Number of newly added jobs
* Total execution time
* Any execution errors

### Success Response Example

```json
{
  "running": false,
  "result": {
    "number_of_data_newly_added": 29,
    "time_taken_seconds": 208.02
  },
  "error": null
}
```

### Running Response Example

```json
{
  "running": true,
  "result": null,
  "error": null
}
```

### Error Response Example

```json
{
  "running": false,
  "result": null,
  "error": "database is locked"
}
```

### Response Fields

| Field                               | Type          | Description                                           |
| ----------------------------------- | ------------- | ----------------------------------------------------- |
| `running`                           | boolean       | Indicates whether the pipeline is currently executing |
| `result`                            | object | null | Pipeline result after completion                      |
| `result.number_of_data_newly_added` | integer       | Number of newly inserted job records                  |
| `result.time_taken_seconds`         | float         | Total pipeline execution time                         |
| `error`                             | string | null | Error message if execution failed                     |

---

## Recommended Workflow

### Step 1 — Start Update Pipeline

Request:

```http
GET /api/updates
```

Expected Response:

```json
{
  "message": "Pipeline started in background",
  "data": {
    "status": "running"
  }
}
```

### Step 2 — Monitor Progress

Request:

```http
GET /api/updates/status
```

Keep polling until:

```json
{
  "running": true,
  "result": null,
  "error": null
}
```

### Step 3 — Read Final Result

Example:

```json
{
  "running": false,
  "result": {
    "number_of_data_newly_added": 29,
    "time_taken_seconds": 208.02
  },
  "error": null
}
```
