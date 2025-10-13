# ✅ Scrape Runs Page - Fixed!

## Wat Was Het Probleem?

1. **Oude test runs** met status "running" bleven hangen
2. **Datum veld mismatch**: API gebruikte `created_at` maar database heeft `started_at`
3. **Hardcoded template data**: "5 minutes ago" en "54%" waren hardcoded
4. **Power BI run niet gevonden**: Scrape is waarschijnlijk niet gestart

## Wat Is Gefixed?

### 1. ✅ API Datum Velden
- Changed `created_at` → `started_at` in API responses
- Frontend krijgt nu correcte timestamps
- `formatDate()` functie werkt nu correct

### 2. ✅ Template Updates
- Verwijderd hardcoded "5 minutes ago"
- Verwijderd hardcoded "54%" progress
- Gebruikt nu `formatDate(run.started_at)` voor echte tijd
- Progress bar toont "Running..." voor actieve scrapes

### 3. ✅ Cleanup Script
Created `cleanup_stuck_runs.py` voor toekomstig gebruik:
```bash
./venv/bin/python cleanup_stuck_runs.py
```

## 🧪 Test Nu

### Stap 1: Refresh Browser
```
http://localhost:8000/runs
```
Hard refresh: **Cmd + Shift + R**

### Stap 2: Bekijk Active Tab
Je zou nu moeten zien:
- ✅ "test" in test - Started X hours ago
- ✅ "test dedup" in test - Started X hours ago
- ✅ Echte timestamps (niet "5 minutes ago")
- ✅ Correcte status

### Stap 3: Bekijk Recent Tab
- Toont runs van laatste 24 uur
- Inclusief completed runs

### Stap 4: Start Nieuwe Scrape
```
http://localhost:8000/queries
→ New Query
→ Query: "Power BI"
→ Location: "België"
→ Lookback: 7
→ Save & Run Now
```

## 🔍 Power BI Run Niet Gevonden

Je "power bi" run is **niet in de database**. Mogelijke oorzaken:

### Check 1: Server Logs
Kijk in terminal waar server draait:
```
# Zou moeten zien:
INFO | Starting immediate scrape: 'Power BI' in 'België'
```

### Check 2: Error in Console
Open browser console (F12) en check voor errors:
```javascript
// Zou moeten zien:
createAndRun called
Query data: {search_query: "Power BI", ...}
Response status: 200
```

### Check 3: Database
```bash
./venv/bin/python -c "
from database import db
runs = db.get_scrape_runs(limit=5)
for r in runs:
    print(f'{r[\"search_query\"]} - {r[\"status\"]}')
"
```

## 🚀 Start Nieuwe Scrape (Correct)

### Via Web Interface
1. Go to: http://localhost:8000/queries
2. Click "New Query"
3. Fill in:
   - Query Text: **Power BI Developer**
   - Location: **België**
   - Lookback Days: **7**
4. Click **"Save & Run Now"**
5. Watch for:
   - ✅ Alert: "Scrape started!"
   - ✅ Redirect to `/runs`
   - ✅ New run appears in Active tab

### Via API (Debug)
```bash
curl -X POST http://localhost:8000/api/queries/run-now \
  -H "Content-Type: application/json" \
  -d '{
    "search_query": "Power BI Developer",
    "location_query": "België",
    "lookback_days": 7,
    "is_active": true
  }'
```

Should return:
```json
{
  "message": "Scrape started successfully",
  "query": {...},
  "status": "running"
}
```

## 📊 Expected Behavior Now

### Active Tab
```
┌─────────────────────────────────────────┐
│ 🟢 RUNNING                              │
├─────────────────────────────────────────┤
│ "Power BI Developer" in België          │
│ Started 2 minutes ago                   │  ← Real timestamp!
│                                         │
│ Progress: Running...                    │  ← No fake percentage
│ ████████████████████████████████        │
│                                         │
│ 0 Jobs Found | 0 New | 0 Updated       │  ← Real data
└─────────────────────────────────────────┘
```

### Recent Tab (24h)
Shows all runs from last 24 hours, including:
- ✅ Data Analyst in Belgium
- ✅ Machine Learning Engineer in Netherlands
- ✅ Data Scientist in Belgium
- ✅ + Your new Power BI run

### Success Tab
Shows only completed runs with status badges

### Failed Tab
Shows failed runs (if any)

## 🐛 Troubleshooting

### Run Niet Zichtbaar

**Check API:**
```bash
curl http://localhost:8000/api/runs/active
```

**Check Database:**
```bash
./venv/bin/python -c "
from database import db
print('Total runs:', len(db.get_scrape_runs()))
print('Running:', len(db.get_scrape_runs(status='running')))
"
```

### Timestamps Nog Steeds Verkeerd

**Hard refresh browser:**
```
Cmd + Shift + R (Mac)
Ctrl + Shift + R (Windows)
```

**Clear cache:**
```javascript
// In browser console:
localStorage.clear();
location.reload(true);
```

### Scrape Start Maar Geen Data

**Check Bright Data API:**
```bash
# In .env file:
echo $BRIGHTDATA_API_KEY
```

**Check Server Logs:**
Look for errors like:
- `BRIGHTDATA_API_KEY not set`
- `Connection refused`
- `Rate limit exceeded`

## ✅ Verification Checklist

- [ ] Refresh browser (hard refresh)
- [ ] Active tab shows real timestamps
- [ ] No more "5 minutes ago" hardcoded text
- [ ] No more "54%" hardcoded progress
- [ ] Recent tab shows last 24h runs
- [ ] Success tab shows completed runs
- [ ] Can start new scrape from queries page
- [ ] New scrape appears in Active tab
- [ ] Auto-refresh works (every 5 seconds)

## 📝 Summary

**Fixed:**
- ✅ API now returns `started_at` as `created_at`
- ✅ Template uses real timestamps
- ✅ Progress bar shows "Running..." not fake percentage
- ✅ formatDate() function works correctly
- ✅ Cleanup script available for stuck runs

**Next Steps:**
1. Hard refresh browser
2. Start new "Power BI" scrape
3. Monitor in Active tab
4. Check results in Jobs page

**Test it now:**
```
http://localhost:8000/runs
```

🎉 **Runs page should now show real data!**
