# Re-enrichment Script voor Oude Data Jobs

## Overzicht

Dit script herverrijkt alle actieve Data jobs die gepost zijn vóór **5 december 2025**. Het gebruikt exact hetzelfde enrichment proces als de nachtelijke automatische enrichment.

## Bestanden

1. **`analyze_old_jobs_for_reenrichment.sql`** - SQL queries om de scope te analyseren
2. **`reenrich_old_data_jobs.py`** - Het hoofdscript voor re-enrichment
3. **`README_REENRICHMENT.md`** - Deze documentatie

## Stap 1: Analyseer de Scope

Voer eerst de analyse query uit om te zien hoeveel jobs er zijn:

```bash
# Kopieer de SQL uit analyze_old_jobs_for_reenrichment.sql
# en voer uit in Supabase SQL Editor
```

De query toont:
- **Totaal aantal jobs** die voldoen aan criteria
- **Hoeveel al verrijkt zijn** (enrichment_completed_at IS NOT NULL)
- **Hoeveel nog niet verrijkt zijn**
- **Hoeveel errors hebben**
- **Breakdown per maand**

### Verwachte Output

```
total_jobs | already_enriched | not_enriched | has_errors | oldest_job | newest_job
-----------+------------------+--------------+------------+------------+------------
     1234  |             890  |          344 |         45 | 2024-01-15 | 2025-12-04
```

## Stap 2: Test met Dry Run

Voer eerst een **dry run** uit om te zien wat er zou gebeuren:

```bash
cd /Users/louisvandeputte/datarole
python scripts/reenrich_old_data_jobs.py --dry-run
```

Dit toont:
- Hoeveel jobs gevonden zijn
- Hoeveel al verrijkt zijn
- Hoeveel errors hebben
- **Geen daadwerkelijke enrichment** (alleen simulatie)

### Verwachte Output

```
================================================================================
RE-ENRICHMENT SCRIPT FOR OLD DATA JOBS
================================================================================
Cutoff date: 2025-12-05
Dry run: True
...
Found 1234 jobs matching criteria
Job breakdown:
  - Already enriched: 890
  - Not enriched: 344
  - Has errors: 45
...
```

## Stap 3: Test met Kleine Batch

Test met een kleine batch (bijv. 10 jobs):

```bash
python scripts/reenrich_old_data_jobs.py --limit 10
```

Dit zal:
- De eerste 10 jobs verrijken
- Vragen om bevestiging voordat het start
- Gedetailleerde logs tonen
- Een logfile aanmaken

### Verwachte Output

```
⚠️  About to re-enrich 10 jobs. This will:
   - Make LLM API calls (costs money)
   - Take approximately 0.3 minutes

Proceed? (yes/no): yes

[1/10] 🆕 Enriching (not yet enriched): Senior Data Analyst
[1/10] ✅ Successfully enriched: Senior Data Analyst
Waiting 1.5s before next job...
...
```

## Stap 4: Volledige Re-enrichment

Als de test succesvol is, voer dan de volledige re-enrichment uit:

### Optie A: Alleen Niet-Verrijkte Jobs (Aanbevolen)

```bash
python scripts/reenrich_old_data_jobs.py
```

Dit verrijkt alleen jobs die:
- Nog niet verrijkt zijn (enrichment_completed_at IS NULL)
- OF een error hebben

### Optie B: Force Re-enrich Alles

```bash
python scripts/reenrich_old_data_jobs.py --force
```

Dit verrijkt **ALLE** jobs, zelfs als ze al verrijkt zijn.

⚠️ **Waarschuwing**: Dit kost meer geld en tijd!

### Optie C: Skip Jobs met Errors

```bash
python scripts/reenrich_old_data_jobs.py --skip-errors
```

Dit slaat jobs over die al een enrichment error hebben.

## Command Line Opties

| Optie | Beschrijving | Default |
|-------|-------------|---------|
| `--dry-run` | Simuleer zonder daadwerkelijk te verrijken | False |
| `--limit N` | Beperk tot eerste N jobs | Geen (alles) |
| `--batch-size N` | Aantal jobs per batch | 50 |
| `--delay SECS` | Vertraging tussen jobs (rate limiting) | 1.5 |
| `--force` | Force re-enrich zelfs als al verrijkt | False |
| `--skip-errors` | Skip jobs met bestaande errors | False |
| `--cutoff-date` | Cutoff datum (YYYY-MM-DD) | 2025-12-05 |

## Voorbeelden

### 1. Dry Run voor Analyse
```bash
python scripts/reenrich_old_data_jobs.py --dry-run
```

### 2. Test met 10 Jobs
```bash
python scripts/reenrich_old_data_jobs.py --limit 10
```

### 3. Verrijk Eerste 100 Jobs met 2s Delay
```bash
python scripts/reenrich_old_data_jobs.py --limit 100 --delay 2.0
```

### 4. Force Re-enrich Alles (Voorzichtig!)
```bash
python scripts/reenrich_old_data_jobs.py --force
```

### 5. Alleen Nieuwe Jobs (Skip Errors)
```bash
python scripts/reenrich_old_data_jobs.py --skip-errors
```

### 6. Andere Cutoff Datum
```bash
python scripts/reenrich_old_data_jobs.py --cutoff-date 2025-11-01
```

## Output en Logging

Het script maakt twee logfiles aan:

1. **`reenrich_old_jobs_YYYYMMDD_HHMMSS.log`** - Volledige log met alle details
2. **`reenrich_errors_YYYYMMDD_HHMMSS.log`** - Alleen errors (als er errors zijn)

### Voorbeeld Log Output

```
2026-01-06 18:30:15 | INFO     | [1/1234] 🆕 Enriching (not yet enriched): Senior Data Analyst
2026-01-06 18:30:17 | SUCCESS  | [1/1234] ✅ Successfully enriched: Senior Data Analyst
2026-01-06 18:30:17 | DEBUG    | Waiting 1.5s before next job...
2026-01-06 18:30:19 | INFO     | [2/1234] 🔄 Re-enriching (had error): Data Engineer
2026-01-06 18:30:21 | SUCCESS  | [2/1234] ✅ Successfully enriched: Data Engineer
...
2026-01-06 18:40:30 | INFO     | Progress: 10/1234 jobs | 9 successful | 1 failed | 615s elapsed
```

### Voorbeeld Summary

```
================================================================================
RE-ENRICHMENT SUMMARY
================================================================================
Total jobs processed: 1234
✅ Successful: 1189
⏭️  Skipped: 0
❌ Failed: 45
⚠️  Rate limited: 3
⏱️  Duration: 1850.5s (30.8 minutes)
📊 Average time per job: 1.6s

❌ First 5 errors:
  1. Data Scientist - ML: Rate limit exceeded
  2. Senior Analytics Engineer: Invalid description format
  3. BI Developer: LLM enrichment failed
  4. Data Architect: Quota exceeded
  5. ML Engineer: Connection timeout
================================================================================
```

## Wat Doet het Script Exact?

Het script volgt exact hetzelfde proces als de nachtelijke auto-enrichment:

1. **Query jobs** met `posted_date < cutoff_date` en `title_classification = 'Data'`
2. **Check enrichment status** voor elke job
3. Voor elke job:
   - Haal job description op uit `job_descriptions` tabel
   - Roep LLM enrichment aan (`enrich_job_with_llm`)
   - Parse en valideer de response
   - Sla enrichment data op in `llm_enrichment` tabel
   - Process tech stack (programming languages + ecosystems)
   - Maak job assignments aan in `job_programming_languages` en `job_ecosystems`
4. **Rate limiting**: 1.5s delay tussen elke job (configureerbaar)
5. **Error handling**: Catch en log alle errors, continue met volgende job
6. **Progress tracking**: Log elke 10 jobs de voortgang

## Technische Details

### Dependencies

Het script gebruikt:
- `database.client.db` - Database client (Supabase)
- `ingestion.llm_enrichment.process_job_enrichment` - Main enrichment functie
- `loguru` - Logging

### Enrichment Process

De `process_job_enrichment` functie:

1. **Check if already enriched** (tenzij `force=True`)
2. **Get job description** van `job_descriptions.full_description_text`
3. **Call LLM** via `enrich_job_with_llm(job_id, description)`
4. **Parse response** en extract:
   - `type_datarol` (Data Analyst, Data Engineer, etc.)
   - `rolniveau` (Junior, Medior, Senior)
   - `seniority` (Entry, Mid, Senior, Lead)
   - `contract` (Permanent, Freelance, etc.)
   - `sourcing_type` (Direct, Recruitment)
   - `labels` (Remote, Hybrid, etc.)
   - Samenvattingen (kort + lang, NL/EN/FR)
   - Responsibilities, Requirements, Offerings (NL/EN/FR)
   - Tech stack (must_have + nice_to_have languages + ecosystems)
   - Spoken languages (must_have + nice_to_have)
5. **Save to database** in `llm_enrichment` tabel
6. **Process tech stack** via `process_tech_stack_for_job`:
   - Upsert programming languages naar `programming_languages`
   - Upsert ecosystems naar `ecosystems`
   - Create assignments in `job_programming_languages`
   - Create assignments in `job_ecosystems`

### Error Handling

Het script handelt de volgende errors af:

- **Rate limit errors**: Logged als rate_limited, continue met volgende job
- **Quota errors**: Logged als error, continue met volgende job
- **Invalid description**: Logged als error, continue met volgende job
- **LLM parsing errors**: Logged als error, continue met volgende job
- **Database errors**: Logged als error, continue met volgende job
- **Network errors**: Logged als error, continue met volgende job

Alle errors worden:
- Gelogd naar console met `logger.error()`
- Opgeslagen in `reenrich_errors_YYYYMMDD_HHMMSS.log`
- Toegevoegd aan de summary statistics

## Kosten Schatting

### LLM API Kosten

Gebaseerd op OpenAI GPT-4 pricing:
- **Input**: ~$0.03 per 1K tokens
- **Output**: ~$0.06 per 1K tokens
- **Gemiddeld per job**: ~3K input + 1K output = ~$0.15 per job

Voor 1000 jobs: **~$150**

### Tijd Schatting

- **Gemiddelde tijd per job**: ~1.5-2 seconden
- **1000 jobs**: ~25-35 minuten
- **Met 1.5s delay**: ~40-50 minuten totaal

## Troubleshooting

### "No jobs found matching criteria"

- Check de cutoff date: `--cutoff-date 2025-12-05`
- Verify dat er jobs zijn met `title_classification = 'Data'`
- Run de SQL analyse query eerst

### "Rate limit exceeded"

- Verhoog de delay: `--delay 2.0` of `--delay 3.0`
- Verklein de batch size: `--batch-size 25`
- Wacht een paar minuten en probeer opnieuw

### "Quota exceeded"

- Check je OpenAI quota/billing
- Wacht tot quota reset (meestal per maand)
- Contact OpenAI support voor quota verhoging

### Script Crasht

- Check de logfile voor details
- Verify database connectie
- Check environment variables (`.env` file)
- Run met `--limit 1` om te testen

### Jobs Worden Geskipped

- Dit is normaal als ze al verrijkt zijn
- Use `--force` om toch te re-enrichen
- Check de enrichment status in database

## Veiligheidsmaatregelen

Het script heeft ingebouwde veiligheidsmaatregelen:

1. **Confirmation prompt** - Vraagt bevestiging voor daadwerkelijke enrichment
2. **Dry run mode** - Test zonder daadwerkelijk te verrijken
3. **Rate limiting** - Voorkomt API rate limits
4. **Error handling** - Continue bij errors, crash niet
5. **Batch processing** - Verwerk in batches met pauzes
6. **Progress tracking** - Log elke 10 jobs de voortgang
7. **Detailed logging** - Alle acties worden gelogd
8. **Error log** - Aparte error log voor troubleshooting

## Best Practices

1. **Start altijd met dry run**: `--dry-run`
2. **Test met kleine batch**: `--limit 10`
3. **Monitor de logs**: Check de logfile tijdens uitvoering
4. **Check kosten**: Bereken geschatte kosten vooraf
5. **Backup database**: Maak backup voordat je force re-enrich
6. **Run tijdens off-peak**: Minder kans op rate limits
7. **Monitor OpenAI quota**: Check je quota vooraf
8. **Save logs**: Bewaar logs voor troubleshooting

## Support

Bij problemen:
1. Check de logfiles
2. Run de SQL analyse query
3. Test met `--limit 1`
4. Check database connectie
5. Verify OpenAI API key en quota
