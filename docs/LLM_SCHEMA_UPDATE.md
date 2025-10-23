# LLM Parser Schema Update

## Overview
Updated the LLM enrichment schema to include new fields and modified existing ones based on the latest parser requirements.

## Changes Made

### 1. Database Migration (`004_update_llm_enrichment_schema.sql`)

**New Columns Added:**
- `type_datarol` - TEXT (enum: Data Engineer, Data Analyst, Data Scientist, BI Developer, Data Architect, Data Governance, Other, NIS)
- `rolniveau` - TEXT[] (array: Technical, Lead, Managerial)
- `seniority` - TEXT[] (array: Junior, Medior, Senior)
- `contract` - TEXT[] (array: Vast, Freelance, Intern)
- `sourcing_type` - TEXT (enum: Direct, Agency)
- `samenvatting_kort` - TEXT (short summary)
- `samenvatting_lang` - TEXT (long summary)
- `must_have_programmeertalen` - TEXT[]
- `nice_to_have_programmeertalen` - TEXT[]
- `must_have_ecosystemen` - TEXT[]
- `nice_to_have_ecosystemen` - TEXT[]
- `must_have_talen` - TEXT[]
- `nice_to_have_talen` - TEXT[]

**Constraints Added:**
- CHECK constraint on `type_datarol` for valid enum values
- CHECK constraint on `sourcing_type` for valid enum values

**Indexes Created:**
- `idx_llm_type_datarol` - For filtering by role type
- `idx_llm_sourcing_type` - For filtering by sourcing type
- `idx_llm_rolniveau` - GIN index for array filtering
- `idx_llm_seniority` - GIN index for array filtering
- `idx_llm_contract` - GIN index for array filtering

### 2. Backend Code (`ingestion/llm_enrichment.py`)

**Updated `save_enrichment_to_db` function:**
- Added all new fields to the database insert/update
- Properly handles arrays for rolniveau, seniority, contract
- Includes summaries (kort and lang)
- Includes sourcing_type

### 3. Frontend (`web/templates/job_detail.html`)

**Enhanced AI Enrichment Tab:**

**Role Classification Card:**
- Type (existing)
- Role Level - Now displays as badges (Technical, Lead, Managerial)
- Seniority - New! Displays as badges (Junior, Medior, Senior)
- Sourcing - New! Shows Direct or Agency

**New Summaries Card:**
- Short Summary (samenvatting_kort)
- Detailed Summary (samenvatting_lang)
- Full-width card with proper text display

**Existing Cards (Updated):**
- Contract Types - Array display with badges
- Programming Languages - Must have / Nice to have
- Ecosystems & Tools - Must have / Nice to have
- Spoken Languages - Required / Preferred

## Migration Instructions

### Run the SQL Migration:

```sql
-- In Supabase SQL Editor, run:
-- /database/migrations/004_update_llm_enrichment_schema.sql
```

### Restart the Application:

```bash
cd /Users/louisvandeputte/datarole
lsof -ti:8000 | xargs kill -9 2>/dev/null
python run_web.py &
```

## New Schema Structure

```json
{
  "type_datarol": "Data Engineer",
  "rolniveau": ["Technical", "Lead"],
  "seniority": ["Medior", "Senior"],
  "contract": ["Vast", "Freelance"],
  "sourcing_type": "Direct",
  "samenvatting_kort": "Short summary text...",
  "samenvatting_lang": "Detailed summary text...",
  "must_have_programmeertalen": ["Python", "SQL"],
  "nice_to_have_programmeertalen": ["Scala"],
  "must_have_ecosystemen": ["AWS", "Databricks"],
  "nice_to_have_ecosystemen": ["Azure"],
  "must_have_talen": ["Dutch", "English"],
  "nice_to_have_talen": ["French"]
}
```

## UI Preview

### Role Classification Card:
```
┌─────────────────────────────────┐
│ Role Classification             │
├─────────────────────────────────┤
│ Type: Data Engineer             │
│ Role Level: [Technical] [Lead] │
│ Seniority: [Medior] [Senior]   │
│ Sourcing: Direct                │
└─────────────────────────────────┘
```

### Summaries Card:
```
┌──────────────────────────────────────────┐
│ AI Summaries                             │
├──────────────────────────────────────────┤
│ Short Summary:                           │
│ Brief description of the role...         │
│                                          │
│ Detailed Summary:                        │
│ Comprehensive analysis of the position...│
└──────────────────────────────────────────┘
```

## Testing

1. **Enrich a Job:**
   - Go to Job Detail page
   - Click "AI Enrichment" tab
   - Click "Enrich Now"
   - Verify all new fields are populated

2. **Verify Display:**
   - Check Role Classification shows all 4 fields
   - Check Summaries card displays both kort and lang
   - Check arrays display as badges
   - Check sourcing_type shows correctly

3. **Database Check:**
   ```sql
   SELECT 
     type_datarol,
     rolniveau,
     seniority,
     contract,
     sourcing_type,
     samenvatting_kort
   FROM llm_enrichment
   WHERE enrichment_completed_at IS NOT NULL
   LIMIT 5;
   ```

## Notes

- **Backward Compatible:** Existing enrichment records will have NULL for new fields
- **Array Fields:** PostgreSQL arrays are properly handled with TEXT[] type
- **Enum Validation:** Database constraints ensure only valid values are stored
- **UI Responsive:** All cards are responsive and work on mobile devices
- **Performance:** GIN indexes enable fast filtering on array fields

## Future Enhancements

1. **Filtering:** Add filters in Jobs page for new fields
2. **Bulk Update:** Re-enrich old jobs with new schema
3. **Analytics:** Dashboard showing distribution of role types, seniority, etc.
4. **Export:** Include new fields in CSV/Excel exports
