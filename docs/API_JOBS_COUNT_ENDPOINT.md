# Jobs Count API Endpoint

## Overview
The `/api/jobs/count` endpoint provides a fast way to get the total number of jobs matching specific filters without loading the actual job data.

## Endpoint
```
GET /api/jobs/count
```

## Use Cases
- Display total job count in UI headers
- Show filtered results count before loading data
- Update counters when filters change
- Pagination total count

## Parameters
All filter parameters from the main `/api/jobs` endpoint are supported:

### Search & Basic Filters
- `search` (string): Full-text search across job titles and descriptions
- `company` (string): Filter by company name
- `location` (string): Filter by location name
- `source` (string): Filter by job source (`linkedin` or `indeed`)
- `is_active` (boolean): Filter active/inactive jobs

### ID-based Filters
- `company_ids` (string): Comma-separated company IDs
- `location_ids` (string): Comma-separated location IDs
- `type_ids` (string): Comma-separated job type IDs
- `run_id` (string): Filter by specific scrape run

### Classification Filters
- `type_datarol` (string): Data role type (e.g., "Data Engineer", "Data Analyst")
- `contract` (string): Contract type from AI enrichment (e.g., "Permanent", "Freelance")
- `seniority` (array): Seniority levels (e.g., "Junior", "Senior")
- `employment` (array): Employment types
- `employment_type` (string): Specific employment type
- `title_classification` (string): Job title classification

### Location Filters
- `subdivision_name_en` (string): Province/region in English (e.g., "Flemish Brabant", "Brussels")

### Date Filters
- `posted_date` (string): Relative date filter (`today`, `week`, `month`, `all`)
- `date_from` (string): Start date (ISO format)
- `date_to` (string): End date (ISO format)

### AI Enrichment
- `ai_enriched` (string): Filter by AI enrichment status (`true`, `false`)

## Response Format
```json
{
  "count": 1234
}
```

## Examples

### Get total active jobs
```bash
GET /api/jobs/count?is_active=true
```
Response:
```json
{
  "count": 5432
}
```

### Count jobs by data role type
```bash
GET /api/jobs/count?type_datarol=Data%20Engineer
```
Response:
```json
{
  "count": 234
}
```

### Count jobs from specific source
```bash
GET /api/jobs/count?source=indeed
```
Response:
```json
{
  "count": 1567
}
```

### Count with multiple filters
```bash
GET /api/jobs/count?type_datarol=Data%20Analyst&source=linkedin&is_active=true
```
Response:
```json
{
  "count": 89
}
```

### Count jobs from specific scrape run
```bash
GET /api/jobs/count?run_id=3a640a9b-388d-4739-abf5-4b53b9b316f6
```
Response:
```json
{
  "count": 42
}
```

### Count by contract type
```bash
GET /api/jobs/count?contract=Permanent
```
Response:
```json
{
  "count": 3456
}
```

### Count by province/region
```bash
GET /api/jobs/count?subdivision_name_en=Flemish%20Brabant
```
Response:
```json
{
  "count": 789
}
```

### Combine multiple filters (type + contract + region)
```bash
GET /api/jobs/count?type_datarol=Data%20Engineer&contract=Freelance&subdivision_name_en=Brussels
```
Response:
```json
{
  "count": 23
}
```

## Frontend Integration

### JavaScript/Fetch Example
```javascript
async function getJobCount(filters = {}) {
  const params = new URLSearchParams(filters);
  const response = await fetch(`/api/jobs/count?${params}`);
  const data = await response.json();
  return data.count;
}

// Usage
const totalJobs = await getJobCount({ is_active: true });
console.log(`Total active jobs: ${totalJobs}`);

const engineerJobs = await getJobCount({ 
  type_datarol: 'Data Engineer',
  source: 'indeed'
});
console.log(`Indeed Data Engineer jobs: ${engineerJobs}`);
```

### React Example
```jsx
import { useState, useEffect } from 'react';

function JobCounter({ filters }) {
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchCount() {
      setLoading(true);
      const params = new URLSearchParams(filters);
      const response = await fetch(`/api/jobs/count?${params}`);
      const data = await response.json();
      setCount(data.count);
      setLoading(false);
    }
    fetchCount();
  }, [filters]);

  if (loading) return <span>Loading...</span>;
  return <span>{count.toLocaleString()} jobs</span>;
}
```

### Vue Example
```vue
<template>
  <div>
    <span v-if="loading">Loading...</span>
    <span v-else>{{ count.toLocaleString() }} jobs</span>
  </div>
</template>

<script>
export default {
  props: ['filters'],
  data() {
    return {
      count: 0,
      loading: true
    }
  },
  watch: {
    filters: {
      handler: 'fetchCount',
      deep: true,
      immediate: true
    }
  },
  methods: {
    async fetchCount() {
      this.loading = true;
      const params = new URLSearchParams(this.filters);
      const response = await fetch(`/api/jobs/count?${params}`);
      const data = await response.json();
      this.count = data.count;
      this.loading = false;
    }
  }
}
</script>
```

## Performance
- **Fast**: Only counts records, doesn't fetch full job data
- **Efficient**: Uses database COUNT query with indexes
- **Lightweight**: Minimal response payload (just a number)

## Notes
- Count reflects the same filters as `/api/jobs` endpoint
- Uses `vw_job_listings` view for consistent results
- Returns 0 if no jobs match the filters
- All filter combinations are supported

## Related Endpoints
- `GET /api/jobs` - Get paginated job listings with same filters
- `GET /api/jobs/{job_id}` - Get single job details
