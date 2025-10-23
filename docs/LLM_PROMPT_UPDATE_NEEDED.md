# LLM Prompt Update Required

## Issue
The database and code have been updated to support the new enrichment schema, but the OpenAI prompt template needs to be updated to return the new fields.

## Current Status

### ✅ Completed:
- Database schema updated with new columns
- Backend code updated to save new fields
- Frontend UI updated to display new fields
- Rolniveau display fixed (handles both string and array)

### ❌ Missing:
- OpenAI prompt template not yet updated to return new fields

## Required Prompt Template Update

The OpenAI prompt template (ID: `pmpt_68ee0e7890788197b06ced94ab8af4d50759bbe1e2c42f88`) needs to be updated to return this exact schema:

```json
{
  "type_datarol": "Data Engineer",
  "rolniveau": ["Technical", "Lead"],
  "seniority": ["Medior", "Senior"],
  "contract": ["Vast", "Freelance"],
  "sourcing_type": "Direct",
  "samenvatting_kort": "Short summary of the job...",
  "samenvatting_lang": "Detailed summary of the job...",
  "must_have_programmeertalen": ["Python", "SQL"],
  "nice_to_have_programmeertalen": ["Scala"],
  "must_have_ecosystemen": ["AWS", "Databricks"],
  "nice_to_have_ecosystemen": ["Azure"],
  "must_have_talen": ["Dutch", "English"],
  "nice_to_have_talen": ["French"]
}
```

## Field Specifications

### type_datarol (required)
- Type: string
- Enum: "Data Engineer", "Data Analyst", "Data Scientist", "BI Developer", "Data Architect", "Data Governance", "Other", "NIS"

### rolniveau (required)
- Type: array of strings
- Enum values: "Technical", "Lead", "Managerial"
- Can contain multiple values

### seniority (required)
- Type: array of strings
- Enum values: "Junior", "Medior", "Senior"
- Can contain multiple values

### contract (required)
- Type: array of strings
- Enum values: "Vast", "Freelance", "Intern"
- Can contain multiple values

### sourcing_type (required)
- Type: string
- Enum: "Direct", "Agency"

### samenvatting_kort (required)
- Type: string
- Short summary (1-2 sentences)

### samenvatting_lang (required)
- Type: string
- Detailed summary (3-5 sentences)

### must_have_programmeertalen (required)
- Type: array of strings
- Programming languages that are required

### nice_to_have_programmeertalen (required)
- Type: array of strings
- Programming languages that are nice to have

### must_have_ecosystemen (required)
- Type: array of strings
- Platforms/ecosystems that are required (e.g., AWS, Azure, Databricks)

### nice_to_have_ecosystemen (required)
- Type: array of strings
- Platforms/ecosystems that are nice to have

### must_have_talen (required)
- Type: array of strings
- Spoken languages that are required (e.g., Dutch, English, French)

### nice_to_have_talen (required)
- Type: array of strings
- Spoken languages that are nice to have

## Steps to Update Prompt

1. Go to OpenAI Prompt Management
2. Find prompt template: `pmpt_68ee0e7890788197b06ced94ab8af4d50759bbe1e2c42f88`
3. Update the output schema to match the JSON above
4. Create a new version (will be version 8)
5. Update `PROMPT_VERSION` in `/Users/louisvandeputte/datarole/ingestion/llm_enrichment.py`:
   ```python
   PROMPT_VERSION = "8"  # Change from "7" to "8"
   ```
6. Restart the application
7. Test enrichment on a job

## Testing After Update

```bash
# Test enrichment
cd /Users/louisvandeputte/datarole
python3 << 'EOF'
from ingestion.llm_enrichment import process_job_enrichment

# Pick a job ID to test
job_id = "YOUR_JOB_ID_HERE"
result = process_job_enrichment(job_id, force=True)
print(result)
EOF
```

## Current Workaround

The UI has been updated to handle:
- Old data where `rolniveau` is a string (displays as single badge)
- New data where `rolniveau` is an array (displays multiple badges)
- Missing fields (shows "-" or "Not available")

So the app will continue to work, but new enrichments won't have the new fields until the prompt is updated.
