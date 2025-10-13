# 🚀 Quick Start: Scheduling

## 📋 Checklist

### ✅ Stap 1: Database Migration (5 min)
1. Open Supabase SQL Editor
2. Kopieer SQL uit `database/migrations/001_add_search_queries_table.sql`
3. Voer uit
4. Verificatie: `SELECT * FROM search_queries LIMIT 1;`

### ✅ Stap 2: Restart Web App (1 min)
```bash
pkill -f run_web.py
./venv/bin/python run_web.py
```

Verwacht in logs:
```
🚀 Starting DataRoles application
📅 Scheduler started
```

### ✅ Stap 3: Test (2 min)
```bash
# Create query
curl -X POST http://localhost:8000/api/queries/ \
  -H "Content-Type: application/json" \
  -d '{"search_query": "powerbi", "location_query": "Belgium"}'

# Get query ID from response, then schedule it
curl -X POST http://localhost:8000/api/queries/{ID}/schedule \
  -H "Content-Type: application/json" \
  -d '{"schedule_enabled": true, "schedule_type": "interval", "schedule_interval_hours": 6}'
```

## 🎯 Wat Werkt Nu

### Backend (100%)
- ✅ Queries opslaan in database
- ✅ Scheduling configureren via API
- ✅ Automatische scrapes op schema
- ✅ Trigger type tracking (manual/scheduled/api)

### API Endpoints
- `POST /api/queries/` - Create query
- `GET /api/queries/` - List queries
- `GET /api/queries/{id}` - Get query
- `PUT /api/queries/{id}` - Update query
- `DELETE /api/queries/{id}` - Delete query
- `POST /api/queries/{id}/run` - Run manually
- `POST /api/queries/{id}/schedule` - Configure schedule
- `GET /api/queries/{id}/schedule` - Get schedule info

### Schedule Types
1. **Daily**: `{"schedule_type": "daily", "schedule_time": "09:00:00"}`
2. **Interval**: `{"schedule_type": "interval", "schedule_interval_hours": 6}`
3. **Weekly**: `{"schedule_type": "weekly", "schedule_time": "09:00:00", "schedule_days_of_week": [1,3,5]}`

## 📊 Monitoring

### Check Scheduled Jobs
```python
from scheduler import get_scheduler
scheduler = get_scheduler()
for job in scheduler.get_scheduled_jobs():
    print(f"{job.id}: next run at {job.next_run_time}")
```

### Check Trigger Types in Scrape Runs
```sql
SELECT 
    search_query, 
    location_query, 
    trigger_type, 
    started_at 
FROM scrape_runs 
ORDER BY started_at DESC 
LIMIT 10;
```

## 🎨 UI (TODO - Na Database Migration)

Zodra database migration klaar is, implementeer ik:
- Schedule button in queries tabel
- Schedule modal (daily/interval/weekly opties)
- Visual badges voor scheduled queries
- Next run time display
- Trigger type indicator in runs page

## 🐛 Troubleshooting

**"Table search_queries does not exist"**
→ Voer SQL migration uit

**Scheduler start niet**
→ Check: `tail -f /tmp/datarole_web.log`

**Scheduled jobs lopen niet**
→ Check: `schedule_enabled = true` in database

---

**Volgende stap**: Voer database migration uit, dan maak ik de UI af! 🎯
