# Fix: Jobs Without Ranking Scores

## 🔍 Problem
8 active Data jobs had no ranking scores despite being enriched and active.

## 🎯 Root Cause
**`posted_date_corrected` was NULL** in `job_ranking_view` for these jobs.

### Why?
The view used:
```sql
LEAST(js.first_seen_at, jp.posted_date) AS posted_date_corrected
```

**SQL LEAST() returns NULL if ANY input is NULL!**

For these 8 jobs:
- `first_seen_at` existed ✅
- `posted_date` existed ✅  
- But `LEAST()` still returned NULL ❌

This caused the ranking system to skip these jobs because `posted_date_corrected` is required for freshness scoring.

## ✅ Solution
Updated view to use `COALESCE` to handle NULLs:

```sql
LEAST(
    COALESCE(js.first_seen_at, jp.posted_date),
    COALESCE(jp.posted_date, js.first_seen_at)
) AS posted_date_corrected
```

Now:
- If `first_seen_at` is NULL → use `posted_date`
- If `posted_date` is NULL → use `first_seen_at`
- If both exist → use the minimum (earliest date)
- **Never returns NULL** ✅

## 📋 Action Required

### 1. Run Migration in Supabase SQL Editor

Go to: **Supabase Dashboard → SQL Editor**

Paste and run:
```sql
-- Migration 073: Fix posted_date_corrected NULL handling

DROP VIEW IF EXISTS job_ranking_view;

CREATE OR REPLACE VIEW job_ranking_view AS
SELECT 
    jp.id,
    jp.title,
    jp.company_id,
    jp.location_id,
    jp.posted_date,
    jp.seniority_level,
    jp.employment_type,
    jp.function_areas,
    jp.base_salary_min,
    jp.base_salary_max,
    jp.apply_url,
    jp.num_applicants,
    jp.is_active,
    jp.title_classification,
    
    -- Fixed: Handle NULL values with COALESCE
    LEAST(
        COALESCE(js.first_seen_at, jp.posted_date),
        COALESCE(jp.posted_date, js.first_seen_at)
    ) AS posted_date_corrected,
    
    c.name as company_name,
    c.industry as company_industry,
    c.company_url,
    c.logo_data as company_logo_data,
    c.employee_count_range as company_employee_count_range,
    c.rating as company_rating,
    c.reviews_count as company_reviews_count,
    
    cmd.hiring_model,
    
    l.city as location_city,
    
    e.enrichment_completed_at,
    e.type_datarol as data_role_type,
    e.hard_skills as skills_must_have,
    e.samenvatting_kort_nl as samenvatting_kort,
    e.samenvatting_lang_nl as samenvatting_lang,
    e.must_have_programmeertalen,
    e.nice_to_have_programmeertalen,
    e.must_have_ecosystemen,
    e.nice_to_have_ecosystemen,
    e.labels,
    
    jd.full_description_text as description_text
    
FROM job_postings jp
LEFT JOIN companies c ON jp.company_id = c.id
LEFT JOIN company_master_data cmd ON c.id = cmd.company_id
LEFT JOIN locations l ON jp.location_id = l.id
LEFT JOIN llm_enrichment e ON jp.id = e.job_posting_id
LEFT JOIN job_descriptions jd ON jp.id = jd.job_posting_id
LEFT JOIN LATERAL (
    SELECT MIN(first_seen_at) as first_seen_at
    FROM job_sources
    WHERE job_posting_id = jp.id
) js ON true
WHERE jp.is_active = true;

COMMENT ON VIEW job_ranking_view IS 'Denormalized view for job ranking with all necessary joins pre-computed. Includes all active jobs (Data, NIS, Other) for ranking. NIS jobs will be assigned rank 999999. posted_date_corrected provides accurate job age by taking minimum of first_seen_at and posted_date, with NULL handling via COALESCE.';
```

### 2. Run Manual Ranking

After migration, run:
```bash
cd /Users/louisvandeputte/datarole
source venv/bin/activate
PYTHONPATH=/Users/louisvandeputte/datarole python ranking/run_ranking_manual.py
```

This will score all 8 jobs that were previously skipped.

### 3. Verify Fix

Check that all jobs now have scores:
```bash
python -c "from database.client import db; result = db.client.table('job_postings').select('id', count='exact').is_('ranking_score', 'null').eq('is_active', True).eq('title_classification', 'Data').execute(); print(f'Jobs without scores: {result.count}')"
```

Expected output: `Jobs without scores: 0`

## 📊 Affected Jobs

These 8 jobs will get scores after the fix:

1. **Senior Product Owner AML Transaction Monitoring** (HNM Solutions)
2. **Data-analist** (PostNL Belgium)
3. **Technical Solution Architect (Data Platform)** (Sciensano)
4. **Senior Engineer, Enabling Analytics** (myGwork)
5. **Analist Managementrapporteringen** (KBC)
6. **Researcher for E-Textiles and Wearables** (imec)
7. **HR Data & Insights Manager** (Egov Select)
8. **Financial Planning & Analysis Partner** (UCB)

## 🔄 Prevention

The scheduler runs ranking **every hour**, so new jobs will be scored automatically. This fix ensures that jobs with NULL `first_seen_at` or `posted_date` will still get a valid `posted_date_corrected`.

## 📝 Technical Details

**Investigation Steps:**
1. ✅ Confirmed jobs were enriched
2. ✅ Confirmed jobs were in `job_ranking_view`
3. ❌ Found jobs were NOT loaded by `load_jobs_from_database()`
4. ❌ Root cause: `posted_date_corrected` was NULL

**Why it matters:**
- Freshness score calculation requires `posted_date_corrected`
- Jobs without this field are skipped during ranking
- This affects the "MEGA BOOST" for jobs ≤30 hours old

**Files Modified:**
- `/database/migrations/073_fix_posted_date_corrected_null.sql` (new)
- Investigation scripts (for debugging)
