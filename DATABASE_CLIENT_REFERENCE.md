# Database Client Quick Reference

## Import

```python
from database import db
```

## Companies

```python
# Insert or update company (deduplication by linkedin_company_id)
company_id = db.upsert_company({
    "linkedin_company_id": "12345",
    "name": "Tech Corp",
    "industry": "Information Technology",
    "company_url": "https://linkedin.com/company/...",
    "logo_url": "https://...",
    "employee_count_range": "51-200"
})

# Get company by LinkedIn ID
company = db.get_company_by_linkedin_id("12345")
```

## Locations

```python
# Get or create location
location = db.get_location_by_string("Amsterdam, Netherlands")
if not location:
    location_id = db.insert_location({
        "full_location_string": "Amsterdam, Netherlands",
        "city": "Amsterdam",
        "country_code": "NL"
    })
```

## Job Postings

```python
# Check if job exists
job = db.get_job_by_linkedin_id("67890")

# Insert new job
job_id = db.insert_job_posting({
    "linkedin_job_id": "67890",
    "company_id": str(company_id),
    "location_id": str(location_id),
    "title": "Senior Data Engineer",
    "seniority_level": "Mid-Senior level",
    "employment_type": "Full-time",
    "industries": ["IT"],
    "function_areas": ["Engineering"],
    "posted_date": "2025-10-09T12:00:00Z",
    "num_applicants": 42,
    "job_url": "https://linkedin.com/jobs/view/67890",
    "is_active": True
})

# Update job
db.update_job_posting(job_id, {
    "num_applicants": 100,
    "last_seen_at": datetime.utcnow().isoformat()
})

# Mark jobs inactive (bulk)
db.mark_jobs_inactive([job_id_1, job_id_2, job_id_3])
```

## Job Descriptions

```python
# Insert description
desc_id = db.insert_job_description({
    "job_posting_id": str(job_id),
    "summary": "Short summary...",
    "full_description_text": "Full text...",
    "full_description_html": "<div>...</div>"
})
```

## Job Posters

```python
# Insert recruiter info
poster_id = db.insert_job_poster({
    "job_posting_id": str(job_id),
    "name": "Jane Recruiter",
    "title": "Technical Recruiter",
    "profile_url": "https://linkedin.com/in/..."
})
```

## Scrape Runs

```python
# Create scrape run
run_id = db.create_scrape_run({
    "search_query": "data engineer",
    "location_query": "Netherlands",
    "platform": "linkedin_brightdata",
    "status": "running",
    "metadata": {"snapshot_id": "abc123"}
})

# Update run with results
db.update_scrape_run(run_id, {
    "status": "completed",
    "completed_at": datetime.utcnow().isoformat(),
    "jobs_found": 150,
    "jobs_new": 25,
    "jobs_updated": 10,
    "jobs_deactivated": 5
})

# Get recent runs
runs = db.get_scrape_runs(status="completed", limit=10)

# Get last successful run for a query
last_run = db.get_last_successful_run(
    query="data engineer",
    location="Netherlands"
)
```

## Scrape History

```python
# Link job to scrape run
db.insert_scrape_history(job_id, run_id)
```

## LLM Enrichment

```python
# Create stub for future AI processing
enrichment_id = db.insert_llm_enrichment_stub(job_id)
```

## Statistics

```python
# Get dashboard stats
stats = db.get_stats()
# Returns:
# {
#     "total_jobs": 1234,
#     "active_jobs": 890,
#     "total_companies": 456,
#     "runs_last_7_days": 12
# }
```

## Job Search

```python
# Search with filters
jobs, total_count = db.search_jobs(
    search_query="engineer",      # Text search in title
    location="Amsterdam",          # Not implemented yet
    seniority="Mid-Senior level",  # Exact match
    active_only=True,              # Only active jobs
    limit=50,                      # Results per page
    offset=0                       # Pagination offset
)

# Jobs include joined company and location data
for job in jobs:
    print(f"{job['title']} at {job['companies']['name']}")
    print(f"Location: {job['locations']['full_location_string']}")
```

## Connection Testing

```python
# Test database connection
if db.test_connection():
    print("Connected!")
```

## Common Patterns

### Upsert Company (Avoid Duplicates)

```python
company_id = db.upsert_company({
    "linkedin_company_id": linkedin_id,
    "name": company_name,
    # ... other fields
})
# Returns existing ID if company exists, new ID if inserted
```

### Get or Create Location

```python
location = db.get_location_by_string(location_string)
if not location:
    location_id = db.insert_location({
        "full_location_string": location_string,
        # ... parse city, country, etc.
    })
else:
    location_id = UUID(location["id"])
```

### Complete Job Ingestion

```python
# 1. Upsert company
company_id = db.upsert_company(company_data)

# 2. Get or create location
location = db.get_location_by_string(location_string)
if not location:
    location_id = db.insert_location(location_data)
else:
    location_id = UUID(location["id"])

# 3. Check if job exists
existing_job = db.get_job_by_linkedin_id(linkedin_job_id)

if not existing_job:
    # Insert new job
    job_id = db.insert_job_posting(job_data)
    db.insert_job_description(description_data)
    if poster_data:
        db.insert_job_poster(poster_data)
    db.insert_llm_enrichment_stub(job_id)
else:
    # Update existing job
    job_id = UUID(existing_job["id"])
    db.update_job_posting(job_id, {
        "last_seen_at": datetime.utcnow().isoformat(),
        "num_applicants": new_applicant_count
    })

# 4. Link to scrape run
db.insert_scrape_history(job_id, run_id)
```

## Error Handling

```python
from loguru import logger

try:
    job_id = db.insert_job_posting(job_data)
except Exception as e:
    logger.error(f"Failed to insert job: {e}")
    # Handle error...
```

## Type Hints

All methods have full type hints:

```python
def insert_job_posting(self, data: Dict[str, Any]) -> UUID
def get_job_by_linkedin_id(self, linkedin_job_id: str) -> Optional[Dict]
def search_jobs(self, ...) -> tuple[List[Dict], int]
```
