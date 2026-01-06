# Quick Start: Re-enrichment van Oude Data Jobs

## TL;DR - Snelle Start

```bash
cd /Users/louisvandeputte/datarole

# 1. Analyse (SQL in Supabase)
# Voer analyze_old_jobs_for_reenrichment.sql uit

# 2. Dry run (test zonder enrichment)
python scripts/reenrich_old_data_jobs.py --dry-run

# 3. Test met 10 jobs
python scripts/reenrich_old_data_jobs.py --limit 10

# 4. Volledige run (alleen niet-verrijkte jobs)
python scripts/reenrich_old_data_jobs.py
```

## Meest Gebruikte Commands

### Analyse
```bash
# Voer SQL uit in Supabase SQL Editor
# File: scripts/analyze_old_jobs_for_reenrichment.sql
```

### Dry Run (Geen Enrichment)
```bash
python scripts/reenrich_old_data_jobs.py --dry-run
```

### Test Runs
```bash
# Test met 10 jobs
python scripts/reenrich_old_data_jobs.py --limit 10

# Test met 50 jobs
python scripts/reenrich_old_data_jobs.py --limit 50
```

### Production Runs
```bash
# Alleen niet-verrijkte jobs (AANBEVOLEN)
python scripts/reenrich_old_data_jobs.py

# Force re-enrich alles (VOORZICHTIG - DUUR!)
python scripts/reenrich_old_data_jobs.py --force

# Skip jobs met errors
python scripts/reenrich_old_data_jobs.py --skip-errors
```

### Custom Settings
```bash
# Langzamere rate (2s delay)
python scripts/reenrich_old_data_jobs.py --delay 2.0

# Kleinere batches (25 jobs per batch)
python scripts/reenrich_old_data_jobs.py --batch-size 25

# Andere cutoff datum
python scripts/reenrich_old_data_jobs.py --cutoff-date 2025-11-01
```

## Verwachte Output

### Dry Run
```
Found 1234 jobs matching criteria
Job breakdown:
  - Already enriched: 890
  - Not enriched: 344
  - Has errors: 45
```

### Actual Run
```
⚠️  About to re-enrich 344 jobs. This will:
   - Make LLM API calls (costs money)
   - Take approximately 8.6 minutes

Proceed? (yes/no): yes

[1/344] 🆕 Enriching: Senior Data Analyst
[1/344] ✅ Successfully enriched: Senior Data Analyst
...
Progress: 10/344 jobs | 9 successful | 1 failed | 15s elapsed
```

### Summary
```
================================================================================
RE-ENRICHMENT SUMMARY
================================================================================
Total jobs processed: 344
✅ Successful: 339
⏭️  Skipped: 0
❌ Failed: 5
⚠️  Rate limited: 1
⏱️  Duration: 516.3s (8.6 minutes)
📊 Average time per job: 1.5s
================================================================================
```

## Kosten Schatting

| Jobs | Geschatte Kosten | Geschatte Tijd |
|------|------------------|----------------|
| 10   | ~$1.50          | ~30 sec        |
| 50   | ~$7.50          | ~2 min         |
| 100  | ~$15            | ~4 min         |
| 500  | ~$75            | ~20 min        |
| 1000 | ~$150           | ~40 min        |

*Gebaseerd op GPT-4 pricing: ~$0.15 per job*

## Troubleshooting

| Probleem | Oplossing |
|----------|-----------|
| "No jobs found" | Check cutoff date en SQL query |
| "Rate limit exceeded" | Verhoog delay: `--delay 2.0` |
| "Quota exceeded" | Check OpenAI billing/quota |
| Script crasht | Check logfile, test met `--limit 1` |
| Jobs worden geskipped | Normaal als al verrijkt, use `--force` |

## Logfiles

Het script maakt automatisch logfiles aan:
- `reenrich_old_jobs_YYYYMMDD_HHMMSS.log` - Volledige log
- `reenrich_errors_YYYYMMDD_HHMMSS.log` - Alleen errors

## Veiligheid

✅ Confirmation prompt voor production runs  
✅ Dry run mode beschikbaar  
✅ Rate limiting ingebouwd  
✅ Error handling (crasht niet bij errors)  
✅ Detailed logging  
✅ Batch processing met pauzes  

## Volledige Documentatie

Zie `README_REENRICHMENT.md` voor:
- Gedetailleerde uitleg van alle opties
- Technische details van het enrichment proces
- Best practices
- Uitgebreide troubleshooting guide
