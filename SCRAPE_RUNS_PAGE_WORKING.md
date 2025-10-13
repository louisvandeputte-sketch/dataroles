# ✅ Scrape Runs Page - Nu Live!

## Wat Werkt Nu

De **Scrape Runs** pagina toont nu **echte data** uit de database!

## 🎯 Features

### 1. ✅ Runs Lijst
- Toont alle scrape runs uit database
- Sorteerd op nieuwste eerst
- Toont status (completed, running, failed)
- Toont query details (search_query, location_query)
- Toont resultaten (jobs_found, jobs_new, jobs_updated)

### 2. ✅ Tab Filtering
- **Active**: Toont running scrapes
- **Recent**: Toont runs van laatste 24 uur
- **Success**: Toont completed runs
- **Failed**: Toont failed runs

### 3. ✅ Auto-Refresh
- Refresht elke 5 seconden
- Toont live updates voor active runs
- Geen page reload nodig

### 4. ✅ Stats
- Active runs count
- Completed in last 24h
- Failed in last 24h

## 🧪 Test Het Nu

### Stap 1: Open Scrape Runs Page
```
http://localhost:8000/runs
```

### Stap 2: Bekijk Bestaande Runs
Je zou moeten zien:
- ✅ Data Analyst in Belgium
- ✅ Machine Learning Engineer in Netherlands
- ✅ Data Scientist in Belgium
- ✅ + Alle andere runs uit je database

### Stap 3: Start Nieuwe Scrape
1. Ga naar: http://localhost:8000/queries
2. Klik "New Query"
3. Vul in:
   - Query: `Python Developer`
   - Location: `Amsterdam`
   - Lookback: `3`
4. Klik "Save & Run Now"
5. Wordt automatisch geredirect naar `/runs`

### Stap 4: Monitor Progress
- Nieuwe run verschijnt bovenaan
- Status toont "running" of "completed"
- Jobs count update in real-time
- Auto-refresh elke 5 seconden

## 📊 Data Weergave

### Run Card (Active Tab)
```
┌─────────────────────────────────────────┐
│ 🟢 RUNNING                              │
├─────────────────────────────────────────┤
│ "Python Developer" in Amsterdam         │
│ Started 2 minutes ago                   │
│                                         │
│ Progress: ████████░░ 54%                │
│                                         │
│ 32 Jobs Found | 20 New | 12 Updated    │
│                                         │
│ API Calls: 12/100 • Rate limit: OK     │
└─────────────────────────────────────────┘
```

### History Table (Other Tabs)
```
Status    | Query              | Location  | Started      | Duration | Results
----------|-------------------|-----------|--------------|----------|-------------
✅ Success | Data Analyst      | Belgium   | 2 hours ago  | 6.5s     | 5 found
✅ Success | ML Engineer       | Netherlands| 2 hours ago  | 6.5s     | 5 found
✅ Success | Data Scientist    | Belgium   | 2 hours ago  | 6.5s     | 5 found
```

## 🔄 Complete Workflow

### End-to-End Test

1. **Create Query**
   ```
   Query: "Data Engineer"
   Location: "België"
   Lookback: 7 days
   ```

2. **Start Scrape**
   - Click "Save & Run Now"
   - Alert: "Scrape started!"
   - Redirect to `/runs`

3. **Monitor Progress**
   - See run in "Active" tab
   - Status: "running"
   - Progress updates every 5 seconds

4. **View Results**
   - Status changes to "completed"
   - See jobs_found, jobs_new, jobs_updated
   - Click "View Details" for more info

5. **Check Jobs**
   - Go to `/jobs` page
   - Filter by company/location
   - See newly scraped jobs

## 📡 API Endpoints Working

### GET /api/runs/
```bash
curl http://localhost:8000/api/runs/
```
Returns:
```json
{
  "runs": [
    {
      "id": "uuid",
      "search_query": "Data Analyst",
      "location_query": "Belgium",
      "status": "completed",
      "created_at": "2025-10-09T19:03:57Z",
      "jobs_found": 5,
      "jobs_new": 0,
      "jobs_updated": 0,
      "metadata": {...}
    }
  ],
  "total": 3,
  "stats": {
    "active_runs": 0,
    "completed_24h": 3,
    "failed_24h": 0
  }
}
```

### GET /api/runs/active
```bash
curl http://localhost:8000/api/runs/active
```
Returns only running scrapes.

## 🎨 UI Features

### Status Badges
- 🟢 **Running**: Green badge with pulse animation
- ✅ **Completed**: Green badge
- ❌ **Failed**: Red badge
- ⚠️ **Partial**: Yellow badge

### Progress Indicators
- Progress bar (for active runs)
- Duration counter
- Jobs found counter
- API rate limit status

### Actions
- **View Details**: See full run information
- **View Live Log**: See execution logs (coming soon)
- **Stop Scrape**: Cancel running scrape (coming soon)

## 🔍 Filtering & Search

### Tab Filters
```javascript
// Active - only running
status === 'running'

// Recent - last 24 hours
created_at > (now - 24h)

// Success - completed
status === 'completed'

// Failed - errors
status === 'failed'
```

### Future Filters
- Date range picker
- Query text search
- Location filter
- Sort by duration/jobs found

## 📈 Stats Dashboard

### Current Stats
- **Active Runs**: Count of running scrapes
- **Completed 24h**: Successful runs today
- **Failed 24h**: Failed runs today

### Future Stats
- Total jobs scraped
- Average duration
- Success rate
- API usage

## 🐛 Troubleshooting

### No Runs Showing

**Check:**
1. Database has runs:
   ```bash
   ./venv/bin/python -c "from database import db; print(len(db.get_scrape_runs()))"
   ```

2. API returns data:
   ```bash
   curl http://localhost:8000/api/runs/
   ```

3. Browser console for errors (F12)

### Runs Not Updating

**Check:**
1. Auto-refresh is working (every 5 seconds)
2. Browser console shows API calls
3. Server is running: `ps aux | grep run_web.py`

### Status Stuck on "Running"

**Possible causes:**
1. Scrape actually still running (check server logs)
2. Scrape crashed (check database status field)
3. Status not updated (manual fix needed)

**Fix:**
```sql
-- In Supabase SQL editor:
UPDATE scrape_runs 
SET status = 'completed' 
WHERE status = 'running' 
AND completed_at IS NOT NULL;
```

## 🚀 Next Enhancements

### Phase 5.2 Features
- [ ] WebSocket for real-time updates
- [ ] Live log streaming
- [ ] Progress percentage calculation
- [ ] Cancel running scrape
- [ ] Retry failed scrape
- [ ] Export run results
- [ ] Run comparison
- [ ] Performance graphs

### UI Improvements
- [ ] Better empty states
- [ ] Loading skeletons
- [ ] Toast notifications
- [ ] Detailed error messages
- [ ] Run timeline view
- [ ] Gantt chart for multiple runs

## 📊 Database Schema

### scrape_runs Table
```sql
id                UUID PRIMARY KEY
search_query      TEXT
location_query    TEXT
status            TEXT (running, completed, failed, partial)
created_at        TIMESTAMPTZ
completed_at      TIMESTAMPTZ
jobs_found        INTEGER
jobs_new          INTEGER
jobs_updated      INTEGER
metadata          JSONB
```

### Metadata Fields
```json
{
  "date_range": "past_week",
  "lookback_days": 7,
  "duration_seconds": 45.2,
  "snapshot_id": "mock_snapshot_abc123",
  "batch_summary": "New: 32, Updated: 15, Skipped: 0, Errors: 0",
  "error_message": null
}
```

## ✅ Success Checklist

- [x] API endpoints return real data
- [x] Runs page displays database runs
- [x] Tab filtering works
- [x] Auto-refresh every 5 seconds
- [x] Stats calculated correctly
- [x] Status badges show correct colors
- [x] Date formatting works
- [x] New scrapes appear immediately
- [x] Redirect from queries page works

## 🎉 Summary

**Scrape Runs page is fully functional!**

You can now:
1. ✅ View all scrape runs from database
2. ✅ Monitor active scrapes in real-time
3. ✅ Filter by status (active/recent/success/failed)
4. ✅ See detailed run information
5. ✅ Track jobs found/new/updated
6. ✅ Auto-refresh for live updates

**Test it now:**
```
http://localhost:8000/runs
```

**Start a new scrape:**
```
http://localhost:8000/queries
→ New Query
→ Fill form
→ Save & Run Now
→ Monitor on /runs page!
```

🚀 **Happy monitoring!**
