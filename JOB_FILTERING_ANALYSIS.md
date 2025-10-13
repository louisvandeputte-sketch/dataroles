# 🔍 Job Filtering Analysis

## ✅ Wat Werkt Goed

### 1. Bright Data Scraping
- ✅ **Bright Data returnt relevante jobs**
- ✅ Query "Data Engineer" → krijgt Data Engineer, Data Analist, Analytics Engineer jobs
- ✅ Location filter werkt (jobs uit Gent/omgeving)
- ✅ Time range filter werkt (past week)

### 2. Database Storage
- ✅ **Jobs worden correct opgeslagen**
- ✅ `job_scrape_history` linkt jobs aan scrape runs
- ✅ Metadata bevat search query info

## ❌ Wat Niet Werkt

### Jobs Page Toont ALLE Jobs

**Probleem:**
Wanneer je naar `/jobs` gaat, zie je ALLE jobs uit de database, niet gefilterd op je search query.

**Voorbeeld:**
```
Query: "Data Engineer" in Gent
Scrape result: 88 relevante Data Engineer jobs

Maar op /jobs pagina:
- Medewerker P&O (van oude scrape)
- Projectleider Openbare Ruimte (van oude scrape)  
- Servicedeskmedewerker (van oude scrape)
- ... + 88 Data Engineer jobs
```

## 🎯 Verwacht Gedrag vs Actueel Gedrag

### Scenario 1: Direct Na Scrape

**Verwacht:**
```
User scraped: "Data Engineer" in "Gent"
→ Gaat naar /jobs
→ Ziet ALLEEN Data Engineer jobs uit Gent
```

**Actueel:**
```
User scraped: "Data Engineer" in "Gent"  
→ Gaat naar /jobs
→ Ziet ALLE jobs (ook oude irrelevante jobs)
```

### Scenario 2: Meerdere Scrapes

**Verwacht:**
```
Scrape 1: "Data Engineer" in "Gent" → 88 jobs
Scrape 2: "Power BI" in "Antwerpen" → 50 jobs

/jobs pagina:
- Heeft filters om te kiezen welke jobs te tonen
- Default: toon alle jobs
- Filter op search query: "Data Engineer" → 88 jobs
- Filter op location: "Gent" → jobs uit Gent
```

**Actueel:**
```
/jobs pagina:
- Toont alle 138 jobs gemixed
- Geen filter op original search query
- Search box zoekt in job title, maar niet op original query
```

## 🔧 Oplossingen

### Optie A: Filter Op Run ID (Simpel)

**Implementatie:**
```
/jobs?run_id=xxx
→ Toont alleen jobs van die specifieke scrape run
```

**Voordelen:**
- ✅ Simpel te implementeren
- ✅ Exacte match met scrape
- ✅ Al geïmplementeerd in "View Jobs" button in run details

**Nadelen:**
- ❌ Moet run_id kennen
- ❌ Niet intuïtief voor user

### Optie B: Smart Default Filter (Aanbevolen)

**Implementatie:**
1. Track "laatste scrape run" in session/localStorage
2. Default filter jobs page op laatste run
3. Toon banner: "Showing jobs from: Data Engineer in Gent" met [Clear filter] button

**Voordelen:**
- ✅ Intuïtief gedrag
- ✅ User ziet direct relevante jobs
- ✅ Kan filter clearen om alle jobs te zien

**Nadelen:**
- ❌ Meer complex
- ❌ Vereist session management

### Optie C: Enhanced Search Filters (Compleet)

**Implementatie:**
1. Voeg "Original Query" filter toe aan jobs page
2. Voeg "Scrape Run" dropdown toe
3. Voeg "Date Scraped" filter toe

**UI:**
```
Filters:
┌─────────────────────────────────────────┐
│ Search: [____________]                  │
│ Original Query: [Data Engineer ▼]      │
│ Location: [Gent ▼]                      │
│ Scrape Run: [Latest ▼]                  │
│ Date Scraped: [Last 7 days ▼]          │
│ Seniority: [All ▼]                      │
│ Employment: [All ▼]                     │
│ [x] Active Only                         │
└─────────────────────────────────────────┘
```

**Voordelen:**
- ✅ Meest flexibel
- ✅ Power users kunnen filteren zoals ze willen
- ✅ Duidelijk welke jobs van welke query komen

**Nadelen:**
- ❌ Meeste werk
- ❌ UI kan overweldigend worden

## 📊 Huidige Database Schema

### Jobs Zijn Gelinkt Aan Runs

```sql
job_scrape_history
├── job_posting_id (FK → job_postings)
├── scrape_run_id (FK → scrape_runs)
└── detected_at

scrape_runs
├── id
├── search_query ("Data Engineer")
├── location_query ("Gent")
├── status
└── metadata (date_range, lookback_days, etc.)
```

**Dit betekent:**
- ✅ We kunnen jobs filteren op scrape run
- ✅ We kunnen original search query ophalen
- ✅ We kunnen jobs groeperen per query

## 🎯 Aanbevolen Implementatie

### Fase 1: Quick Fix (Nu)

**Voeg "View Jobs" link toe na scrape:**
```
Scrape completed!
88 jobs found for "Data Engineer" in Gent

[View These Jobs] → /jobs?run_id=xxx
```

**Code changes:**
1. ✅ Al geïmplementeerd in run details modal
2. Voeg toe aan scrape completion notification
3. Voeg toe aan runs list

### Fase 2: Smart Filters (Later)

**Voeg filters toe aan /jobs:**
```javascript
filters: {
  search: '',
  originalQuery: null,  // NEW
  location: null,
  scrapeRun: null,      // NEW
  seniority: null,
  employment: null,
  activeOnly: true
}
```

**API changes:**
```python
@router.get("/jobs")
async def list_jobs(
    search: Optional[str] = None,
    run_id: Optional[str] = None,  # NEW
    original_query: Optional[str] = None,  # NEW
    location: Optional[str] = None,
    ...
):
    # Filter jobs based on run_id or original_query
    if run_id:
        job_ids = get_jobs_from_run(run_id)
        query = query.in_('id', job_ids)
    elif original_query:
        # Find runs with this query
        runs = get_runs_by_query(original_query)
        job_ids = get_jobs_from_runs(runs)
        query = query.in_('id', job_ids)
```

## 🧪 Test Scenario

### Test 1: Scrape "Data Engineer"
```
1. Start scrape: "Data Engineer" in "Gent"
2. Wait for completion (88 jobs)
3. Click "View Jobs" in run details
4. ✅ Should see ONLY Data Engineer jobs
5. ✅ Should see banner: "Filtered by: Data Engineer in Gent"
6. Click [Clear Filter]
7. ✅ Should see ALL jobs
```

### Test 2: Multiple Scrapes
```
1. Scrape "Data Engineer" in "Gent" → 88 jobs
2. Scrape "Power BI" in "Antwerpen" → 50 jobs
3. Go to /jobs
4. ✅ Should see all 138 jobs
5. Filter by "Original Query: Data Engineer"
6. ✅ Should see 88 jobs
7. Filter by "Original Query: Power BI"
8. ✅ Should see 50 jobs
```

## 📝 Conclusie

**Huidige Situatie:**
- ✅ Bright Data werkt correct
- ✅ Jobs worden correct opgeslagen
- ❌ Jobs page toont alle jobs zonder context

**Oplossing:**
1. **Nu**: Gebruik "View Jobs" button in run details (al geïmplementeerd)
2. **Later**: Voeg smart filters toe aan jobs page

**Prioriteit:**
- 🔴 **High**: Documenteer dat users "View Jobs" moeten gebruiken
- 🟡 **Medium**: Voeg "Original Query" filter toe
- 🟢 **Low**: Smart default filtering

---

**Voor nu: Gebruik de "View Jobs" button in de run details modal!** 🎯
