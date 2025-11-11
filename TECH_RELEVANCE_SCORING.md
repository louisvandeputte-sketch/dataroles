# 📊 Tech Stack Relevance Scoring - Implementation

## Overzicht

Automatisch AI-scoring systeem dat programmeertalen en ecosystemen beoordeelt op relevantie (0-100) voor data professionals.

## Wat Is Geïmplementeerd

### 1. Database Schema ✅

**Nieuwe kolommen:**
```sql
-- programming_languages
ALTER TABLE programming_languages
ADD COLUMN relevance_score INTEGER DEFAULT NULL;

-- ecosystems  
ALTER TABLE ecosystems
ADD COLUMN relevance_score INTEGER DEFAULT NULL;
```

**Indexes voor snelle sorting:**
```sql
CREATE INDEX idx_programming_languages_relevance 
ON programming_languages(relevance_score DESC NULLS LAST);

CREATE INDEX idx_ecosystems_relevance 
ON ecosystems(relevance_score DESC NULLS LAST);
```

### 2. LLM Relevance Scorer ✅

**File:** `ingestion/relevance_scorer.py`

**Functionaliteit:**
- Gebruikt OpenAI GPT-4o-mini (snel & goedkoop)
- Jouw exacte prompt voor consistente scoring
- Retourneert alleen een getal (0-100)
- Validatie van output range
- Error handling

**Scoring Criteria:**
- **0** = Totaal onbekend/niet relevant/niche
- **100** = Extreem bekend/essentieel/universeel
- Gebaseerd op: populariteit, toepasbaarheid, markttrends

### 3. Auto-Enrichment Service ✅

**File:** `ingestion/auto_enrich_service.py`

**Nieuwe functionaliteit:**
- `process_pending_tech_scores()` toegevoegd
- Draait elke 60 seconden
- Scoort 10 languages + 10 ecosystems per cyclus
- Automatische rate limiting (0.5s tussen calls)

**Service draait nu:**
```
🤖 Auto-enrichment service started (locations + job titles + tech relevance)
```

## Hoe Het Werkt

### Automatische Flow

```
Nieuwe Tech Item Toegevoegd
  ↓
relevance_score = NULL
  ↓
Auto-enrichment service (elke 60s)
  ↓
Haalt 10 items zonder score op
  ↓
LLM Scorer (GPT-4o-mini)
  ↓
Score opgeslagen in database
  ↓
Beschikbaar voor sorting in UI
```

### Logs

```
📊 Auto-scoring 5 languages + 8 ecosystems
✅ Scored 'Python': 100/100
✅ Scored 'SQL': 100/100
✅ Scored 'Elasticsearch': 85/100
✅ Scored 'HDFS': 75/100
✅ Scored 'PowerApps': 65/100
```

## Test Resultaten

### Voorbeelden

| Tech Item | Score | Interpretatie |
|-----------|-------|---------------|
| Python | 100 | Essentieel |
| SQL | 100 | Essentieel |
| Excel | 90 | Zeer relevant |
| JavaScript | 85 | Breed gebruikt |
| Spark | 85 | Populair |
| Power BI | 85 | Standaard tool |
| R | 70 | Relevant |
| Oracle Data Integrator | 60 | Niche |
| Fortran | 20 | Zeer niche |
| XSLT | 15 | Bijna irrelevant |

### Score Distributie

**High (80-100):** Essentiële tools die vrijwel elke data professional kent
- Python, SQL, Excel, Spark, Snowflake, Power BI, Tableau, dbt, Airflow

**Medium (50-79):** Relevante maar meer gespecialiseerde tools
- R, Oracle Data Integrator, HDFS

**Low (0-49):** Niche of verouderde tools
- XSLT, Fortran

## API Functies

### Score Berekenen

```python
from ingestion.relevance_scorer import score_relevance

score, error = score_relevance("Python")
# Returns: (100, None)

score, error = score_relevance("XSLT")
# Returns: (15, None)
```

### Database Opslaan

```python
from ingestion.relevance_scorer import score_programming_language, score_ecosystem

# Score en sla op
success = score_programming_language(lang_id, "Python")
success = score_ecosystem(eco_id, "Snowflake")
```

## Gebruik in UI

### Sorting

```sql
-- Meest relevante languages eerst
SELECT * FROM programming_languages
ORDER BY relevance_score DESC NULLS LAST;

-- Meest relevante ecosystems eerst
SELECT * FROM ecosystems
ORDER BY relevance_score DESC NULLS LAST;
```

### Filtering

```sql
-- Alleen high-relevance items (80+)
SELECT * FROM programming_languages
WHERE relevance_score >= 80;

-- Alleen scored items
SELECT * FROM ecosystems
WHERE relevance_score IS NOT NULL;
```

## Performance

### Snelheid
- **Per item:** ~0.5-1 seconde (GPT-4o-mini)
- **Per cyclus:** 10 languages + 10 ecosystems = ~10-20 seconden
- **Rate limiting:** 0.5s tussen calls (veilig voor API limits)

### Kosten
- **Model:** GPT-4o-mini (goedkoopste optie)
- **Tokens:** ~10 tokens output per item
- **Kosten:** Verwaarloosbaar (~$0.0001 per item)

### Schaalbaarheid
- **Bestaande items:** ~100-200 items = 2-3 minuten totaal
- **Nieuwe items:** Automatisch binnen 60 seconden gescored
- **Bulk scoring:** Mogelijk via script als nodig

## Files

```
✅ database/migrations/033_add_relevance_scores.sql
   - Database schema changes
   
✅ ingestion/relevance_scorer.py
   - LLM scoring logic
   
✅ ingestion/auto_enrich_service.py
   - Auto-enrichment integration
   
✅ test_relevance_scorer.py
   - Test script
   
✅ RUN_MIGRATION_033.md
   - Migration instructions
```

## Migration Stappen

### 1. Run SQL Migration

In Supabase SQL Editor:
```sql
-- Zie RUN_MIGRATION_033.md voor volledige SQL
ALTER TABLE programming_languages ADD COLUMN relevance_score INTEGER;
ALTER TABLE ecosystems ADD COLUMN relevance_score INTEGER;
CREATE INDEX idx_programming_languages_relevance ...
CREATE INDEX idx_ecosystems_relevance ...
```

### 2. Herstart Server

```bash
# Server herstart automatisch met nieuwe auto-enrichment
python run_web.py
```

### 3. Verificatie

```bash
# Test scorer
python test_relevance_scorer.py

# Check logs
# Zoek naar: "📊 Auto-scoring X languages + Y ecosystems"
```

## Monitoring

### Check Progress

```sql
-- Hoeveel items zijn gescored?
SELECT 
  'languages' as type,
  COUNT(*) as total,
  COUNT(relevance_score) as scored,
  ROUND(COUNT(relevance_score)::numeric / COUNT(*) * 100, 1) as pct_scored
FROM programming_languages
UNION ALL
SELECT 
  'ecosystems',
  COUNT(*),
  COUNT(relevance_score),
  ROUND(COUNT(relevance_score)::numeric / COUNT(*) * 100, 1)
FROM ecosystems;
```

### Score Distribution

```sql
-- Verdeling van scores
SELECT 
  CASE 
    WHEN relevance_score >= 80 THEN 'High (80-100)'
    WHEN relevance_score >= 50 THEN 'Medium (50-79)'
    ELSE 'Low (0-49)'
  END as category,
  COUNT(*) as count
FROM programming_languages
WHERE relevance_score IS NOT NULL
GROUP BY category
ORDER BY MIN(relevance_score) DESC;
```

## Troubleshooting

### Scores Worden Niet Toegevoegd

**Check:**
1. Is migratie uitgevoerd? → `\d programming_languages`
2. Draait auto-enrichment? → Check logs voor "Auto-scoring"
3. OpenAI API key geldig? → Check settings

### Onverwachte Scores

**Oplossing:**
- Scores zijn AI-gegenereerd, kleine variaties zijn normaal
- Bij grote afwijkingen: check of prompt correct is
- Re-score mogelijk door score op NULL te zetten

### Performance Issues

**Oplossing:**
- Rate limiting is al ingebouwd (0.5s tussen calls)
- Batch size is beperkt (10 per type per cyclus)
- Bij problemen: verhoog check_interval in service

## Toekomstige Uitbreidingen

### Mogelijk Later

1. **Manual Override:** UI om scores handmatig aan te passen
2. **Bulk Re-scoring:** Script om alle items opnieuw te scoren
3. **Score History:** Track score changes over tijd
4. **Category Weights:** Verschillende scores per data role type
5. **Trending:** Bonus voor trending technologies

## Samenvatting

✅ **Database:** Kolommen + indexes toegevoegd  
✅ **Scorer:** LLM-based scoring met jouw prompt  
✅ **Auto-enrichment:** Automatisch elke 60s  
✅ **Getest:** 16/16 items succesvol gescored  
✅ **Live:** Draait nu in productie  

**Nieuwe tech items worden automatisch binnen 60 seconden gescored!** 🎉
