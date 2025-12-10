# 🛑 Auto-Enrichment Uitschakelen

## Probleem

De auto-enrichment service draait **24/7** in je deployed web app en enriched automatisch:
- Nieuwe Data jobs (elke 60 seconden check)
- Companies zonder enrichment (elke 10 minuten)

**Dit kost veel geld!** Vooral als jobs **opnieuw** enriched worden.

---

## ⚠️ Huidige Situatie

**Waar draait het:**
- In je deployed web app (Heroku/Render/etc.)
- Gestart via `web/app.py` bij FastAPI startup
- Draait continu in de achtergrond

**Wat doet het:**
```python
# Elke 60 seconden:
- Check voor nieuwe Data jobs
- Enrich tot 20 jobs per keer
- 2 seconden delay tussen jobs

# Elke 10 minuten:
- Check voor unenriched companies
- Enrich in batches
```

**Kosten:**
- Elke job enrichment: ~$0.01
- Elke company enrichment: ~$0.02
- **Als jobs opnieuw enriched worden: dubbele kosten!**

---

## ✅ Oplossing: Uitschakelen via Environment Variable

### Stap 1: Voeg Environment Variable Toe

Op je deployment platform (Heroku/Render/etc.):

```bash
DISABLE_AUTO_ENRICHMENT=true
```

### Stap 2: Herstart Je App

De auto-enrichment service zal nu **niet meer draaien**.

---

## 🔧 Alternatieve Oplossingen

### Optie 1: Alleen 's Nachts Enrichen

Voeg tijd-check toe in `ingestion/auto_enrich_service.py`:

```python
async def process_pending_data_jobs(self):
    # Only run between 00:00 and 06:00
    from datetime import datetime
    current_hour = datetime.now().hour
    if not (0 <= current_hour < 6):
        return  # Skip during daytime
    
    # ... rest of code
```

### Optie 2: Minder Frequent Checken

In `ingestion/auto_enrich_service.py`:

```python
def __init__(self):
    self.check_interval = 3600  # Check every hour instead of every minute
```

### Optie 3: Volledig Uitschakelen in Code

In `web/app.py`:

```python
# Set this to True to disable background services
disable_background_services = True
```

---

## 🐛 Bug: Re-Enrichment van Bestaande Jobs

**Probleem:** Jobs worden opnieuw enriched, zelfs als ze al enriched zijn.

**Oorzaak:** LEFT JOIN query geeft mogelijk verkeerde resultaten terug.

**Fix:** Verbeter de query in `auto_enrich_service.py`:

```python
# VOOR (buggy):
result = db.client.table("job_postings")\
    .select("id, title, llm_enrichment!left(enrichment_completed_at)")\
    .eq("title_classification", "Data")\
    .eq("is_active", True)\
    .limit(20)\
    .execute()

# NA (correct):
result = db.client.table("job_postings")\
    .select("id, title")\
    .eq("title_classification", "Data")\
    .eq("is_active", True)\
    .is_("llm_enrichment", "null")\  # Only jobs WITHOUT enrichment
    .limit(20)\
    .execute()
```

---

## 📊 Verificatie

### Check of Auto-Enrichment Uitstaat

```python
import os
print(f"Auto-enrichment disabled: {os.getenv('DISABLE_AUTO_ENRICHMENT')}")
```

### Check Recente Enrichments

```python
from database.client import db
from datetime import datetime, timedelta

# Last hour
one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
recent = db.client.table('llm_enrichment')\
    .select('id', count='exact')\
    .gte('created_at', one_hour_ago)\
    .execute()

print(f"Enrichments last hour: {recent.count}")
# Should be 0 if disabled
```

---

## 💰 Kosten Besparing

**Voor (met auto-enrichment):**
- ~100 jobs/dag × $0.01 = ~$1/dag
- ~30 companies/dag × $0.02 = ~$0.60/dag
- **Totaal: ~$1.60/dag = ~$48/maand**

**Na (uitgeschakeld):**
- Alleen nieuwe jobs 's nachts (scraper)
- ~20 jobs/dag × $0.01 = ~$0.20/dag
- **Totaal: ~$0.20/dag = ~$6/maand**

**Besparing: ~$42/maand** 💰

---

## 🚀 Aanbevolen Setup

1. **Schakel auto-enrichment UIT** via environment variable
2. **Enrich alleen 's nachts** via scraper/scheduler
3. **Monitor kosten** via OpenAI dashboard
4. **Check logs** voor onverwachte enrichments

---

## ✅ Checklist

- [ ] `DISABLE_AUTO_ENRICHMENT=true` toegevoegd aan deployment
- [ ] App herstart
- [ ] Verificatie: geen enrichments in laatste uur
- [ ] OpenAI kosten gedaald
- [ ] Scheduler uitgeschakeld (company enrichment)

---

## 📞 Support

Als je nog steeds onverwachte enrichments ziet:

1. Check OpenAI logs voor timestamps
2. Check database voor recente `llm_enrichment` records
3. Zoek naar andere scripts die `process_job_enrichment` aanroepen
4. Check cron jobs: `crontab -l`
5. Check launchd: `launchctl list | grep -i enrich`
