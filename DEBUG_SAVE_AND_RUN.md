# 🔍 Debug Guide: "Save & Run Now" Button

## Wat Ik Heb Gefixed

### 1. ✅ Input Fields
- **Lookback Days**: Toegevoegd `value="7"` en `x-model.number` voor correcte number binding
- **Radio Buttons**: Toegevoegd `name="status"` en `checked` attribute voor Active

### 2. ✅ JavaScript Validation
- Toegevoegd console logging voor debugging
- Toegevoegd validatie voor required fields
- Betere error messages

### 3. ✅ Server Herstart
Server is herstart met de nieuwe code.

## 🧪 Test Stappen

### Stap 1: Open Browser Console
1. Open **Chrome DevTools** (F12 of Cmd+Option+I)
2. Ga naar **Console** tab
3. Laat deze open tijdens testen

### Stap 2: Refresh Pagina
```
http://localhost:8000/queries
```
Druk op **Cmd+Shift+R** (hard refresh) om cache te clearen

### Stap 3: Open Modal
Klik op **"New Query"** knop

### Stap 4: Vul Formulier In
- **Query Text**: `Test Query`
- **Location**: `Test Location`
- **Lookback Days**: `7` (should be pre-filled)
- **Status**: Active (should be selected)

### Stap 5: Klik "Save & Run Now"

### Wat Je Zou Moeten Zien

#### In Browser Console:
```
createAndRun called
Query data: {search_query: "Test Query", location_query: "Test Location", lookback_days: 7, is_active: true}
Sending request to /api/queries/run-now
Response status: 200
Success response: {message: "Scrape started successfully", ...}
```

#### In Browser:
- Alert box met: "✅ Scrape started!"
- Modal sluit
- Redirect naar `/runs` pagina na 2 seconden

#### In Terminal (waar server draait):
```
INFO | Starting immediate scrape: 'Test Query' in 'Test Location'
```

## 🐛 Troubleshooting

### Probleem 1: Niets gebeurt bij klik

**Check in Console:**
- Zie je `createAndRun called`? 
  - ❌ NEE → Alpine.js werkt niet, refresh pagina
  - ✅ JA → Ga naar volgende check

**Check in Console:**
- Zie je `Query data: {...}`?
  - ❌ NEE → JavaScript error, check console voor errors
  - ✅ JA → Zijn de velden ingevuld?

**Check velden:**
```javascript
// In console, type:
document.querySelector('[x-data]').__x.$data.newQuery
```
Dit toont de query data. Check of `search_query` en `location_query` gevuld zijn.

### Probleem 2: Validation Error

Als je ziet: "❌ Please fill in both Query Text and Location"

**Oplossing:**
- Vul beide velden in
- Check of Alpine.js de waarden correct bind:
  ```javascript
  // In console:
  document.querySelector('input[x-model="newQuery.search_query"]').value
  ```

### Probleem 3: Network Error

Als je ziet in console: `Failed to fetch` of `Network error`

**Check:**
1. Is server running?
   ```bash
   ps aux | grep run_web.py
   ```

2. Test API direct:
   ```bash
   curl -X POST http://localhost:8000/api/queries/run-now \
     -H "Content-Type: application/json" \
     -d '{"search_query":"Test","location_query":"Test","lookback_days":7,"is_active":true}'
   ```

### Probleem 4: API Error (500)

Als je ziet: Response status: 500

**Check terminal logs** voor error details:
```
ERROR | Failed to start scrape: [error message]
```

Mogelijke oorzaken:
- Bright Data API key niet gezet
- Database connection error
- Import error in backend

## 🔧 Quick Fixes

### Fix 1: Hard Refresh Browser
```
Cmd + Shift + R (Mac)
Ctrl + Shift + R (Windows)
```

### Fix 2: Clear Browser Cache
```javascript
// In console:
localStorage.clear();
sessionStorage.clear();
location.reload(true);
```

### Fix 3: Restart Server
```bash
pkill -f run_web.py
./venv/bin/python run_web.py
```

### Fix 4: Check Alpine.js Loading
```javascript
// In console, should return true:
typeof Alpine !== 'undefined'
```

### Fix 5: Check API Endpoint
```bash
# Test if endpoint exists:
curl http://localhost:8000/docs

# Look for POST /api/queries/run-now
```

## 📊 Expected Flow

```
User clicks "Save & Run Now"
    ↓
createAndRun() called
    ↓
Validate fields (search_query, location_query)
    ↓
POST /api/queries/run-now
    ↓
Backend: execute_scrape_run() in background
    ↓
Response: 200 OK with run details
    ↓
Alert shown to user
    ↓
Modal closes
    ↓
Redirect to /runs after 2 seconds
```

## 🎯 Manual Test via Console

Als de button niet werkt, test direct via console:

```javascript
// Get Alpine component
const component = document.querySelector('[x-data]').__x.$data;

// Set query data
component.newQuery = {
    search_query: 'Manual Test',
    location_query: 'Console Test',
    lookback_days: 7,
    is_active: true
};

// Call function directly
component.createAndRun();
```

## 📝 Check Server Logs

In de terminal waar de server draait, zou je moeten zien:

```
INFO:     127.0.0.1:xxxxx - "POST /api/queries/run-now HTTP/1.1" 200 OK
2025-10-09 22:xx:xx.xxx | INFO     | web.api.queries:run_query_now:123 - Starting immediate scrape: 'Test Query' in 'Test Location'
```

## ✅ Success Checklist

- [ ] Browser console shows no errors
- [ ] `createAndRun called` appears in console
- [ ] Query data is logged correctly
- [ ] Request is sent (status 200)
- [ ] Alert appears with success message
- [ ] Modal closes
- [ ] Redirect happens after 2 seconds
- [ ] Server logs show scrape starting

## 🆘 Still Not Working?

### Share These Details:

1. **Browser Console Output** (copy all messages)
2. **Server Terminal Output** (last 20 lines)
3. **Network Tab** in DevTools:
   - Filter by "run-now"
   - Check request/response
4. **Alpine.js Check**:
   ```javascript
   // In console:
   console.log(Alpine.version);
   ```

### Test API Directly:

```bash
# This should work:
curl -X POST http://localhost:8000/api/queries/run-now \
  -H "Content-Type: application/json" \
  -d '{
    "search_query": "Data Engineer",
    "location_query": "België",
    "lookback_days": 7,
    "is_active": true
  }'
```

Expected response:
```json
{
  "message": "Scrape started successfully",
  "query": {
    "search_query": "Data Engineer",
    "location_query": "België",
    "lookback_days": 7
  },
  "status": "running"
}
```

## 🎉 When It Works

You should see:
1. ✅ Console logs showing flow
2. ✅ Alert with scrape details
3. ✅ Redirect to /runs page
4. ✅ Server logs showing scrape starting
5. ✅ (Eventually) Jobs appearing in database

---

**Current Status**: Server restarted with fixes
**Next Step**: Hard refresh browser and try again!
