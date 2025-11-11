# ✅ Indeed & LinkedIn Separation - Implementation

## Probleem

Wanneer je een Indeed scrape run aanmaakt en runt, werd er automatisch ook een LinkedIn scrape getriggerd. Dit was niet gewenst - Indeed queries moeten alleen op Indeed zoeken.

## Oorzaak

De scheduler gebruikte niet de `source` kolom uit de `search_queries` tabel bij het aanroepen van `execute_scrape_run()`, waardoor alle scheduled scrapes defaulted naar `source="linkedin"`.

## Oplossing ✅

### 1. Scheduler Service Update

**File:** `scheduler/service.py`

**Wijzigingen:**
1. ✅ `source` parameter ophalen uit query bij `schedule_query()`
2. ✅ `source` doorgeven aan `_run_scheduled_scrape()` via args
3. ✅ `source` parameter toevoegen aan `_run_scheduled_scrape()` functie signature
4. ✅ `source` doorgeven aan `execute_scrape_run()`

**Code:**
```python
# In schedule_query()
source = query.get("source", "linkedin")  # Get source from query

# In scheduler.add_job()
args=[query_id, search_query, location_query, lookback_days, job_type_id, source]

# In _run_scheduled_scrape()
async def _run_scheduled_scrape(..., source: str = "linkedin"):
    result = await execute_scrape_run(
        ...,
        source=source  # Pass source to scrape
    )
```

## Hoe Het Nu Werkt

### Indeed Queries
```
Indeed Query (source="indeed")
  ↓
Scheduler laadt query met source="indeed"
  ↓
execute_scrape_run(source="indeed")
  ↓
Bright Data Indeed scraper
  ↓
Alleen Indeed jobs
```

### LinkedIn Queries
```
LinkedIn Query (source="linkedin")
  ↓
Scheduler laadt query met source="linkedin"
  ↓
execute_scrape_run(source="linkedin")
  ↓
Bright Data LinkedIn scraper
  ↓
Alleen LinkedIn jobs
```

## Database Schema

### search_queries Table

```sql
CREATE TABLE search_queries (
    id UUID PRIMARY KEY,
    search_query TEXT NOT NULL,
    location_query TEXT NOT NULL,
    source TEXT NOT NULL,  -- 'linkedin' or 'indeed'
    is_active BOOLEAN DEFAULT true,
    schedule_enabled BOOLEAN DEFAULT false,
    schedule_type TEXT,  -- 'daily', 'weekly', 'interval'
    ...
);
```

**Belangrijke kolom:** `source` bepaalt welke platform wordt gebruikt.

## Verificatie

### Test 1: Indeed Query Aanmaken
```
1. Ga naar Indeed Queries page
2. Maak nieuwe query: "Data Engineer" in "Belgium"
3. Source wordt automatisch "indeed"
4. Run de query
5. ✅ Alleen Indeed wordt gescraped
```

### Test 2: Scheduled Indeed Query
```
1. Indeed query met schedule_enabled=true
2. Wacht tot scheduled run
3. Check logs: "🤖 Running scheduled indeed scrape"
4. ✅ Alleen Indeed wordt gescraped
```

### Test 3: LinkedIn Query (Bestaand)
```
1. Bestaande LinkedIn query
2. Run de query
3. ✅ Alleen LinkedIn wordt gescraped (zoals altijd)
```

## Logs

### Voorheen (Incorrect)
```
🤖 Running scheduled scrape: 'Data Engineer' in 'Belgium'
→ Defaulted to LinkedIn, ook al was het een Indeed query
```

### Nu (Correct)
```
🤖 Running scheduled indeed scrape: 'Data Engineer' in 'Belgium'
→ Gebruikt correct source platform
```

## API Endpoints

### Indeed Queries
```python
POST /api/indeed-queries/{query_id}/run
→ execute_scrape_run(source="indeed")
```

### LinkedIn Queries (Regular)
```python
POST /api/queries/{query_id}/run
→ execute_scrape_run(source="linkedin")
```

## Source Flow

```
User Creates Query
  ↓
Source specified in UI/API
  ↓
Saved to search_queries.source
  ↓
Scheduler loads query
  ↓
Scheduler reads source column
  ↓
Passes source to execute_scrape_run()
  ↓
Correct scraper is used
  ↓
Jobs saved with correct source
```

## Files Changed

```
✅ scheduler/service.py
   - Added source parameter extraction
   - Pass source to scheduled scrapes
   - Updated function signature
```

## Geen Breaking Changes

- ✅ Bestaande LinkedIn queries werken nog steeds
- ✅ Default source is "linkedin" (backwards compatible)
- ✅ Indeed queries gebruiken nu correct "indeed"
- ✅ Geen database migraties nodig (source kolom bestaat al)

## Samenvatting

**Voorheen:**
- Indeed query → LinkedIn + Indeed scrape ❌

**Nu:**
- Indeed query → Alleen Indeed scrape ✅
- LinkedIn query → Alleen LinkedIn scrape ✅

**Geen duplicatie meer! Elke query scraped alleen zijn eigen platform.** 🎉
