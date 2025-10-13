# 📅 Scheduling Setup Instructions

## ✅ Wat Is Al Klaar

### Backend (100% Complete)
- ✅ APScheduler geïnstalleerd
- ✅ Scheduler service gemaakt (`scheduler/service.py`)
- ✅ API endpoints voor scheduling (`web/api/queries.py`)
- ✅ Scraper updated voor trigger tracking
- ✅ Web app startup integration

### Database Schema
- ✅ SQL migration script gemaakt
- ⚠️ **JE MOET NOG UITVOEREN** (zie hieronder)

## 🔧 Stap 1: Database Migration Uitvoeren

### SQL Script
Ga naar je Supabase dashboard en voer deze SQL uit:

```sql
-- Migration: Add search_queries table and update scrape_runs

-- Create search_queries table
CREATE TABLE IF NOT EXISTS search_queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    search_query TEXT NOT NULL,
    location_query TEXT NOT NULL,
    lookback_days INTEGER DEFAULT 7,
    is_active BOOLEAN DEFAULT true,
    
    -- Scheduling fields
    schedule_enabled BOOLEAN DEFAULT false,
    schedule_type TEXT,  -- 'daily', 'interval', 'weekly'
    schedule_time TIME,  -- For daily (e.g., 09:00)
    schedule_interval_hours INTEGER,  -- For interval (e.g., 6)
    schedule_days_of_week INTEGER[],  -- For weekly (0=Sunday, 6=Saturday)
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Unique constraint on query+location combination
    UNIQUE(search_query, location_query)
);

-- Add indexes
CREATE INDEX idx_search_queries_active ON search_queries(is_active);
CREATE INDEX idx_search_queries_scheduled ON search_queries(schedule_enabled, next_run_at);
CREATE INDEX idx_search_queries_next_run ON search_queries(next_run_at) WHERE schedule_enabled = true;

-- Add trigger_type to scrape_runs
ALTER TABLE scrape_runs ADD COLUMN IF NOT EXISTS trigger_type TEXT DEFAULT 'manual';

-- Add search_query_id to scrape_runs
ALTER TABLE scrape_runs ADD COLUMN IF NOT EXISTS search_query_id UUID REFERENCES search_queries(id) ON DELETE SET NULL;

-- Create index on trigger_type
CREATE INDEX IF NOT EXISTS idx_scrape_runs_trigger_type ON scrape_runs(trigger_type);

-- Add updated_at trigger to search_queries
CREATE TRIGGER update_search_queries_updated_at
    BEFORE UPDATE ON search_queries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE search_queries IS 'Stored search query configurations with optional scheduling';
COMMENT ON COLUMN scrape_runs.trigger_type IS 'How the scrape was triggered: manual, scheduled, or api';
```

### Verificatie
Na het uitvoeren, check of de tabel bestaat:

```sql
SELECT * FROM search_queries LIMIT 1;
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'search_queries';
```

## 🚀 Stap 2: Migreer Bestaande Queries

Optioneel: Migreer je huidige query+location combinaties naar de nieuwe tabel:

```sql
-- Insert unique query+location combinations from scrape_runs
INSERT INTO search_queries (search_query, location_query, is_active, lookback_days)
SELECT DISTINCT 
    search_query, 
    location_query,
    true as is_active,
    7 as lookback_days
FROM scrape_runs
ON CONFLICT (search_query, location_query) DO NOTHING;
```

## 🧪 Stap 3: Test de Setup

### 1. Start de Web App
```bash
pkill -f run_web.py
./venv/bin/python run_web.py
```

Je zou moeten zien:
```
🚀 Starting DataRoles application
📅 Scheduler started
✅ Scheduler started
```

### 2. Test API Endpoints

**Create a query:**
```bash
curl -X POST http://localhost:8000/api/queries/ \
  -H "Content-Type: application/json" \
  -d '{
    "search_query": "Data Engineer",
    "location_query": "Belgium",
    "lookback_days": 7,
    "is_active": true
  }'
```

**List queries:**
```bash
curl http://localhost:8000/api/queries/ | jq .
```

**Schedule a query (daily at 09:00):**
```bash
curl -X POST http://localhost:8000/api/queries/{QUERY_ID}/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_enabled": true,
    "schedule_type": "daily",
    "schedule_time": "09:00:00"
  }'
```

**Schedule a query (every 6 hours):**
```bash
curl -X POST http://localhost:8000/api/queries/{QUERY_ID}/schedule \
  -H "Content-Type: application/json" \
  -d '{
    "schedule_enabled": true,
    "schedule_type": "interval",
    "schedule_interval_hours": 6
  }'
```

## 📊 Stap 4: UI Updates (TODO)

De UI moet nog worden geüpdatet met:
- ✅ Schedule button in actions menu
- ✅ Schedule modal
- ✅ Visual indicators (badges voor scheduled queries)
- ✅ Next run time display

Dit kan ik implementeren zodra de database migration is uitgevoerd.

## 🔍 Monitoring

### Check Scheduled Jobs
```python
from scheduler import get_scheduler

scheduler = get_scheduler()
jobs = scheduler.get_scheduled_jobs()

for job in jobs:
    print(f"Job: {job.id}")
    print(f"  Next run: {job.next_run_time}")
    print(f"  Trigger: {job.trigger}")
```

### Check Logs
```bash
tail -f /tmp/datarole_web.log | grep -E "Scheduled|🤖|📅"
```

## 📝 Schedule Types

### Daily
Runs every day at a specific time:
```json
{
  "schedule_enabled": true,
  "schedule_type": "daily",
  "schedule_time": "09:00:00"
}
```

### Interval
Runs every X hours:
```json
{
  "schedule_enabled": true,
  "schedule_type": "interval",
  "schedule_interval_hours": 6
}
```

### Weekly
Runs on specific days at a specific time:
```json
{
  "schedule_enabled": true,
  "schedule_type": "weekly",
  "schedule_time": "09:00:00",
  "schedule_days_of_week": [1, 3, 5]  // Monday, Wednesday, Friday
}
```

## 🎯 Next Steps

1. **Voer de SQL migration uit** in Supabase
2. **Restart de web app** om scheduler te starten
3. **Test de API endpoints** zoals hierboven
4. **Laat me weten** als het werkt, dan maak ik de UI af!

## ❓ Troubleshooting

### "Table search_queries does not exist"
→ Voer de SQL migration uit in Supabase

### "Scheduler not starting"
→ Check logs: `tail -f /tmp/datarole_web.log`

### "No scheduled jobs running"
→ Check if queries have `schedule_enabled = true` in database

---

**Status**: Backend 100% klaar, wacht op database migration ✅
