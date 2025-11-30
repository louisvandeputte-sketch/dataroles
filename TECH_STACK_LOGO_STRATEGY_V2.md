# Tech Stack Logo Integration Strategy V2

## 🚨 Performance Issue Discovered

Initial testing shows:
- Language lookup: **~294ms**
- Ecosystem lookup: **~211ms**
- **Total per job: ~843ms** (4 subqueries)
- **For 20 jobs: ~17 seconds** ❌

This is **TOO SLOW** for a view with subqueries!

---

## 🎯 Revised Strategy: **Client-Side Join with Cached Lookup Table**

### **Why This is Better:**

1. **Logo data changes rarely** - perfect for caching
2. **Small dataset** - 89 languages + 1014 ecosystems = ~1100 items
3. **One-time fetch** - cache for entire session
4. **Frontend can merge instantly** - in-memory join is microseconds

---

## ✅ **Recommended Approach: Separate Cached Endpoint**

### **Backend: Create Lightweight Lookup View**

```sql
-- Migration 074: Create tech_stack_lookup view for logo data

CREATE OR REPLACE VIEW tech_stack_lookup AS
SELECT 
    name,
    display_name,
    logo_url,
    category,
    'language' AS type
FROM programming_languages
WHERE is_active = TRUE

UNION ALL

SELECT 
    name,
    display_name,
    logo_url,
    category,
    'ecosystem' AS type
FROM ecosystems
WHERE is_active = TRUE;

COMMENT ON VIEW tech_stack_lookup IS 'Lightweight lookup table for tech stack logos. Frontend fetches once and caches. ~1100 rows, ~50KB response.';
```

### **Frontend: Fetch Once, Cache, Merge**

```typescript
// 1. Fetch lookup table once (on app load or lazy)
const techStackLookup = await fetch('/api/tech-stack-lookup')
  .then(r => r.json());

// Create fast lookup maps
const languageLookup = new Map(
  techStackLookup
    .filter(t => t.type === 'language')
    .map(t => [t.name.toLowerCase(), t])
);

const ecosystemLookup = new Map(
  techStackLookup
    .filter(t => t.type === 'ecosystem')
    .map(t => [t.name.toLowerCase(), t])
);

// 2. Fetch jobs (normal vw_job_listings query)
const jobs = await fetch('/api/jobs').then(r => r.json());

// 3. Enrich jobs with logos (instant, in-memory)
const enrichedJobs = jobs.map(job => ({
  ...job,
  must_have_languages_detailed: job.must_have_programmeertalen.map(name => 
    languageLookup.get(name.toLowerCase()) || { name, display_name: name, logo_url: null }
  ),
  must_have_ecosystems_detailed: job.must_have_ecosystemen.map(name =>
    ecosystemLookup.get(name.toLowerCase()) || { name, display_name: name, logo_url: null }
  ),
  // ... same for nice_to_have
}));
```

### **Performance:**

- **Lookup table fetch:** ~100ms (once per session, ~50KB)
- **Jobs fetch:** ~200ms (normal query, no subqueries)
- **Client-side merge:** <1ms (in-memory Map lookup)
- **Total first load:** ~300ms
- **Subsequent loads:** ~200ms (lookup cached)

**vs. Original subquery approach: ~17 seconds for 20 jobs** ❌

---

## 🔄 **Alternative: Pre-compute in Database (Materialized View)**

If you want database-side solution:

```sql
-- Create materialized view with pre-joined data
CREATE MATERIALIZED VIEW mv_job_listings_with_logos AS
SELECT 
    e.job_posting_id,
    -- ... all regular fields ...
    
    -- Pre-computed JSONB with logos
    (
        SELECT jsonb_agg(jsonb_build_object(
            'name', pl.name,
            'display_name', pl.display_name,
            'logo_url', pl.logo_url,
            'category', pl.category
        ))
        FROM unnest(e.must_have_programmeertalen) AS lang
        LEFT JOIN programming_languages pl ON LOWER(pl.name) = LOWER(lang)
    ) AS must_have_languages_detailed
    -- ... etc
FROM llm_enrichment e
-- ... joins ...

-- Refresh every hour (or on-demand)
CREATE INDEX ON mv_job_listings_with_logos(job_posting_id);
```

**Pros:**
- ✅ Fast queries (pre-computed)
- ✅ No client-side logic

**Cons:**
- ❌ Stale data (refresh lag)
- ❌ Extra storage
- ❌ Refresh overhead
- ❌ Complexity (refresh scheduling)

---

## 🏆 **Final Recommendation**

### **Use Client-Side Cached Lookup**

**Implementation:**

1. **Create `tech_stack_lookup` view** (simple UNION of both tables)
2. **Add API endpoint:** `GET /api/tech-stack-lookup`
3. **Frontend:**
   - Fetch lookup table on app load
   - Cache in React Context / Redux / localStorage
   - Merge with job data client-side

**Why:**
- ✅ **Fastest** - no database overhead
- ✅ **Simplest** - no complex views or materialized views
- ✅ **Cacheable** - lookup data rarely changes
- ✅ **Scalable** - works for 1000s of jobs
- ✅ **Flexible** - easy to add more metadata later

**Trade-offs:**
- ⚠️ One extra API call (but cached!)
- ⚠️ Client-side merge logic (but trivial - just Map lookups)

---

## 📋 Implementation Steps

### **1. Create Lookup View**

```sql
-- database/migrations/074_create_tech_stack_lookup_view.sql

CREATE OR REPLACE VIEW tech_stack_lookup AS
SELECT 
    name,
    display_name,
    logo_url,
    category,
    'language' AS type
FROM programming_languages
WHERE is_active = TRUE

UNION ALL

SELECT 
    name,
    display_name,
    logo_url,
    category,
    'ecosystem' AS type
FROM ecosystems
WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_programming_languages_name_lower 
ON programming_languages(LOWER(name));

CREATE INDEX IF NOT EXISTS idx_ecosystems_name_lower 
ON ecosystems(LOWER(name));

COMMENT ON VIEW tech_stack_lookup IS 'Lightweight lookup for tech stack logos. ~1100 rows. Frontend caches this.';
```

### **2. Add API Endpoint**

```python
# web/api/tech_stack.py

from fastapi import APIRouter
from database.client import db

router = APIRouter()

@router.get("/tech-stack-lookup")
async def get_tech_stack_lookup():
    """
    Get all tech stack items with logos for client-side caching.
    Returns ~1100 items (~50KB). Frontend should cache this.
    """
    result = db.client.table("tech_stack_lookup")\
        .select("*")\
        .execute()
    
    return {
        "data": result.data,
        "cache_hint": "max-age=3600"  # Cache for 1 hour
    }
```

### **3. Frontend Hook**

```typescript
// hooks/useTechStackLookup.ts

import { useQuery } from '@tanstack/react-query';

interface TechStackItem {
  name: string;
  display_name: string;
  logo_url: string | null;
  category: string | null;
  type: 'language' | 'ecosystem';
}

export function useTechStackLookup() {
  return useQuery({
    queryKey: ['tech-stack-lookup'],
    queryFn: async () => {
      const response = await fetch('/api/tech-stack-lookup');
      const { data } = await response.json();
      
      // Create fast lookup maps
      const languages = new Map<string, TechStackItem>();
      const ecosystems = new Map<string, TechStackItem>();
      
      data.forEach((item: TechStackItem) => {
        const key = item.name.toLowerCase();
        if (item.type === 'language') {
          languages.set(key, item);
        } else {
          ecosystems.set(key, item);
        }
      });
      
      return { languages, ecosystems };
    },
    staleTime: 1000 * 60 * 60, // 1 hour
    cacheTime: 1000 * 60 * 60 * 24, // 24 hours
  });
}
```

### **4. Enrich Jobs**

```typescript
// utils/enrichJobsWithLogos.ts

export function enrichJobWithLogos(
  job: JobListing,
  lookup: { languages: Map<string, TechStackItem>, ecosystems: Map<string, TechStackItem> }
) {
  return {
    ...job,
    must_have_languages_detailed: job.must_have_programmeertalen?.map(name =>
      lookup.languages.get(name.toLowerCase()) || {
        name,
        display_name: name,
        logo_url: null,
        category: null,
        type: 'language'
      }
    ) || [],
    nice_to_have_languages_detailed: job.nice_to_have_programmeertalen?.map(name =>
      lookup.languages.get(name.toLowerCase()) || {
        name,
        display_name: name,
        logo_url: null,
        category: null,
        type: 'language'
      }
    ) || [],
    must_have_ecosystems_detailed: job.must_have_ecosystemen?.map(name =>
      lookup.ecosystems.get(name.toLowerCase()) || {
        name,
        display_name: name,
        logo_url: null,
        category: null,
        type: 'ecosystem'
      }
    ) || [],
    nice_to_have_ecosystems_detailed: job.nice_to_have_ecosystemen?.map(name =>
      lookup.ecosystems.get(name.toLowerCase()) || {
        name,
        display_name: name,
        logo_url: null,
        category: null,
        type: 'ecosystem'
      }
    ) || [],
  };
}
```

### **5. Usage in Component**

```typescript
// components/JobList.tsx

function JobList() {
  const { data: jobs } = useJobs();
  const { data: lookup } = useTechStackLookup();
  
  if (!jobs || !lookup) return <Loading />;
  
  const enrichedJobs = jobs.map(job => enrichJobWithLogos(job, lookup));
  
  return (
    <div>
      {enrichedJobs.map(job => (
        <JobCard key={job.id} job={job} />
      ))}
    </div>
  );
}
```

---

## 📊 Performance Comparison

| Approach | First Load | Subsequent | Complexity | Stale Data |
|----------|-----------|------------|------------|------------|
| **Subqueries in View** | ~17s | ~17s | Low | No |
| **Materialized View** | ~200ms | ~200ms | High | Yes |
| **Client-Side Cached** | ~300ms | ~200ms | Medium | No |

**Winner:** Client-Side Cached ✅

---

## 🎯 Next Steps

1. Create migration 074 with `tech_stack_lookup` view
2. Add API endpoint
3. Create frontend hook
4. Test with real data
5. Deploy! 🚀
