# 🔧 AI Engineer Type Fix - Root Cause Analysis

## 🎯 Problem Discovered

**Symptom:** 10 "AI Engineer" jobs being re-enriched every hour, causing high costs.

**Root Cause:** Database constraint mismatch with LLM output.

---

## 🔍 Technical Analysis

### Database Constraint (Migration 004)

```sql
ALTER TABLE llm_enrichment
ADD CONSTRAINT check_type_datarol 
CHECK (type_datarol IN (
    'Data Engineer', 
    'Data Analyst', 
    'Data Scientist', 
    'BI Developer', 
    'Data Architect', 
    'Data Governance', 
    'Other', 
    'NIS'
));
```

**Missing:** `'AI Engineer'`

### LLM Behavior

The OpenAI prompt (version 24) can return `"AI Engineer"` as `data_role_type` for jobs like:
- AI Engineer (NLP / ML / Big Data)
- Agentic AI Solutions & Business Translator
- Freelance MLOps & AI Engineers
- GEN AI Engineer
- AI Specialist
- Machine Learning Researcher
- Software Engineer IA
- Founding AI/ML Research Engineer

### The Infinite Loop

```
1. LLM enriches job → returns "AI Engineer"
2. Save to database → CONSTRAINT VIOLATION (23514)
3. type_datarol stays NULL (save fails)
4. retry_failed_enrichments() runs every hour
5. Finds job with NULL type_datarol
6. Re-enriches with force=True
7. Returns "AI Engineer" again
8. CONSTRAINT VIOLATION again
9. → INFINITE LOOP! 💸
```

**Cost:** 10 jobs × $0.01 × 24 hours = **$2.40/day** = **$72/month**

---

## ✅ Solution

### Step 1: Update Database Constraint

**Migration:** `081_add_ai_engineer_to_type_datarol.sql`

```sql
ALTER TABLE llm_enrichment
DROP CONSTRAINT IF EXISTS check_type_datarol;

ALTER TABLE llm_enrichment
ADD CONSTRAINT check_type_datarol 
CHECK (type_datarol IN (
    'Data Engineer', 
    'Data Analyst', 
    'Data Scientist', 
    'BI Developer', 
    'Data Architect', 
    'Data Governance', 
    'AI Engineer',  -- ✅ ADDED
    'Other', 
    'NIS'
));
```

### Step 2: Re-enrich Failed Jobs

After running the migration, re-enrich the 10 stuck jobs:

```python
from ingestion.llm_enrichment import process_job_enrichment

stuck_job_ids = [
    'd68d2252-a20d-4014-9724-52eb53ba47bb',  # AI Engineer (NLP / ML / Big Data)
    'e1ca29f3-a970-4738-9ad6-0d824c4356b3',  # Agentic AI Solutions
    'fb13bb8f-52df-4206-b0d4-3dad41eb3ead',  # Cloud Data & AI Platform Expert
    'd0cfd75f-9762-47cc-a6f0-6c7d26937a9c',  # Data & AI Engineer
    '0cfa13ee-7b01-4b5b-8941-8b99b5a3eaff',  # Freelance MLOps & AI Engineers
    'dfbbd066-53c0-42ad-8c0d-38e4be207dcc',  # GEN AI Engineer
    '4b5f1d95-2a02-44e5-afc7-cf3628a56502',  # AI Specialist
    '2ba44502-4203-4e24-b05b-7143b1681a79',  # Machine Learning Researcher
    '92537c34-573f-4a1a-a548-97808ec8ac32',  # Software Engineer IA
    '35e30737-dc6a-4a7c-bdce-b012847d2b2e',  # Founding AI/ML Research Engineer
]

for job_id in stuck_job_ids:
    result = process_job_enrichment(job_id, force=True)
    print(f"Job {job_id}: {result['success']}")
```

---

## 📋 Action Items

### Immediate (Required)

1. **Run Migration in Supabase Dashboard:**
   - Go to SQL Editor
   - Paste contents of `081_add_ai_engineer_to_type_datarol.sql`
   - Execute

2. **Verify Constraint:**
   ```sql
   SELECT conname, pg_get_constraintdef(oid) 
   FROM pg_constraint 
   WHERE conname = 'check_type_datarol';
   ```

3. **Re-enrich Stuck Jobs:**
   - Use script above or API endpoint
   - Verify `type_datarol` is now set correctly

### Future Prevention

1. **Update OpenAI Prompt:**
   - Document all valid `data_role_type` values
   - Keep in sync with database constraint
   - Version control prompt changes

2. **Add Validation:**
   ```python
   VALID_DATA_ROLE_TYPES = [
       'Data Engineer',
       'Data Analyst', 
       'Data Scientist',
       'BI Developer',
       'Data Architect',
       'Data Governance',
       'AI Engineer',
       'Other',
       'NIS'
   ]
   
   def validate_enrichment_data(data):
       if data.get('data_role_type') not in VALID_DATA_ROLE_TYPES:
           logger.warning(f"Invalid data_role_type: {data.get('data_role_type')}")
           data['data_role_type'] = 'Other'  # Fallback
       return data
   ```

3. **Monitor for New Types:**
   - Check logs for constraint violations
   - Alert when new types appear
   - Update constraint proactively

---

## 🎯 Expected Results

**Before:**
- 10 jobs stuck in infinite loop
- $2.40/day wasted on re-enrichments
- NULL type_datarol for AI jobs

**After:**
- All jobs enriched successfully
- No more re-enrichments
- type_datarol = "AI Engineer" correctly saved
- $0 wasted on retries

---

## 🔗 Related Files

- Migration: `/database/migrations/081_add_ai_engineer_to_type_datarol.sql`
- Original constraint: `/database/migrations/004_update_llm_enrichment_schema.sql`
- Enrichment logic: `/ingestion/llm_enrichment.py`
- Retry logic: `/ingestion/auto_enrich_service.py` (now disabled)

---

## ✅ Verification

After running migration and re-enriching:

```sql
-- Check that AI Engineer jobs are now saved correctly
SELECT 
    job_posting_id,
    type_datarol,
    enrichment_completed_at,
    enrichment_error
FROM llm_enrichment
WHERE job_posting_id IN (
    'd68d2252-a20d-4014-9724-52eb53ba47bb',
    'e1ca29f3-a970-4738-9ad6-0d824c4356b3'
    -- ... other job IDs
);

-- Should show:
-- type_datarol = 'AI Engineer'
-- enrichment_completed_at = recent timestamp
-- enrichment_error = NULL
```
