# 🚀 Bright Data LinkedIn Scraper - Final Setup

## ✅ Je Hebt De Juiste Scraper!

**LinkedIn job listings information - discover by keyword**
- Endpoint: POST
- Mode: Synchronous (Real-time)
- Dataset ID: Zie in Code examples rechtsboven

## 📋 Setup Instructies

### Stap 1: Krijg Je Credentials

1. Klik rechtsboven op **"Code examples"** in Bright Data dashboard
2. Je ziet een curl command zoals:

```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inputs": [...], "dataset_id": "6cfq20f2fdqdb0c3f90aa..."}' \
  https://api.brightdata.com/datasets/v3/trigger
```

3. **Kopieer:**
   - **API Token**: De string na "Bearer " (bijv. `abc123def456...`)
   - **Dataset ID**: De string bij "dataset_id" (bijv. `6cfq20f2fdqdb0c3f90aa...`)

### Stap 2: Open .env File

```bash
cd /Users/louisvandeputte/datarole
nano .env
```

### Stap 3: Voeg Credentials Toe

Vervang deze regels in je .env file:

```bash
# Bright Data Configuration
BRIGHTDATA_API_TOKEN=PLAK_HIER_JE_API_TOKEN
BRIGHTDATA_DATASET_ID=PLAK_HIER_JE_DATASET_ID

# Disable mock API
USE_MOCK_API=false
```

**Voorbeeld:**
```bash
# Bright Data Configuration
BRIGHTDATA_API_TOKEN=abc123def456ghi789jkl012mno345pqr678
BRIGHTDATA_DATASET_ID=6cfq20f2fdqdb0c3f90aa12b34c56d78e90f

# Disable mock API
USE_MOCK_API=false
```

### Stap 4: Save & Exit

- Druk `Ctrl+O` (save)
- Druk `Enter` (confirm)
- Druk `Ctrl+X` (exit)

### Stap 5: Restart Server

```bash
pkill -f run_web.py
./venv/bin/python run_web.py &
```

### Stap 6: Test Met Echte LinkedIn Data!

1. Open browser: `http://localhost:8000/queries`
2. Klik **"New Query"**
3. Vul in:
   - Query: `Data Engineer`
   - Location: `Gent`
   - Lookback: `7`
4. Klik **"Save & Run Now"**

### Stap 7: Wacht Op Resultaten

De scrape kan 30-60 seconden duren. Ga naar:
```
http://localhost:8000/runs
```

Je zou moeten zien:
- Status: Running → Completed
- Jobs found: Echte LinkedIn jobs uit Gent!

### Stap 8: Bekijk Jobs

Ga naar:
```
http://localhost:8000/jobs
```

Je zou nu **echte LinkedIn jobs uit Gent** moeten zien! 🎉

## ✅ Verificatie

Run dit script om te checken:

```bash
./venv/bin/python check_latest_runs.py
```

**Verwacht output:**
```
✅ Real API key configured: abc123def4...
```

**NIET meer:**
```
⚠️  Using MOCK Bright Data client
```

## 🎯 Wat Je Krijgt

### Met Mock (voor):
```
Jobs: Dummy data
- Senior Data Engineer at Tech Corp in Amsterdam
- Data Analyst at Analytics Inc in New York
```

### Met Echte API (na):
```
Jobs: Echte LinkedIn data
- Data Engineer at Proximus in Gent
- Senior Data Engineer at Telenet in Gent
- Data Analyst at Colruyt Group in Gent
```

## 🔍 Troubleshooting

### Error: "Invalid API token"
- Check of je de volledige token hebt gekopieerd
- Geen spaties voor/na de token
- Token moet beginnen met letters/cijfers

### Error: "Dataset not found"
- Check of dataset ID correct is
- Moet beginnen met cijfer/letter
- Geen spaties

### Nog steeds mock data?
```bash
# Check .env file:
cat .env | grep BRIGHTDATA

# Moet tonen:
BRIGHTDATA_API_TOKEN=abc123...
BRIGHTDATA_DATASET_ID=6cfq20...
USE_MOCK_API=false

# Als USE_MOCK_API=true, verander naar false!
```

### Server restart vergeten?
```bash
# Altijd restart na .env changes:
pkill -f run_web.py
./venv/bin/python run_web.py &
```

## 💰 Kosten

### Free Trial Credits
- Je hebt free test credits (7 dagen)
- Gebruik deze om te testen!
- ~100-500 jobs gratis

### Daarna
- Pay-as-you-go
- ~$0.10-0.50 per 100 jobs
- Stel budget in op Bright Data dashboard

## 📊 Expected Flow

```
1. User creates query: "Data Engineer" in "Gent"
   ↓
2. System calls Bright Data API
   ↓
3. Bright Data scrapes LinkedIn.com
   ↓
4. Returns real job listings
   ↓
5. System saves to database
   ↓
6. User sees real Gent jobs in UI! 🎉
```

---

## 🎉 Klaar!

Zodra je:
1. ✅ API Token hebt gekopieerd
2. ✅ Dataset ID hebt gekopieerd
3. ✅ Toegevoegd aan .env
4. ✅ USE_MOCK_API=false gezet
5. ✅ Server herstart

Dan krijg je **echte LinkedIn jobs**! 🚀

**Veel succes!**
