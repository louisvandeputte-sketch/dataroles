# Indeed Dataset ID Setup

## Probleem

Indeed scrape run failed met error:
```
ValueError: BRIGHTDATA_INDEED_DATASET_ID not configured in settings
```

## Oplossing

Je moet de Indeed Dataset ID toevoegen aan je configuratie.

### Stap 1: Verkrijg Indeed Dataset ID van Bright Data

1. Log in op [Bright Data Dashboard](https://brightdata.com/cp/datasets)
2. Ga naar **Datasets** → **Indeed Jobs**
3. Kopieer de **Dataset ID** (bijv. `gd_xxxxxxxxxx`)

### Stap 2: Voeg Toe aan .env

Open `.env` en voeg toe:

```bash
# Indeed Dataset ID (from Bright Data)
BRIGHTDATA_INDEED_DATASET_ID=gd_xxxxxxxxxx
```

**Voorbeeld:**
```bash
# Bright Data
BRIGHTDATA_API_TOKEN=your_api_token_here
BRIGHTDATA_DATASET_ID=gd_lpfll7v5hcqtkxl6l
BRIGHTDATA_INDEED_DATASET_ID=gd_your_indeed_dataset_id_here  # ← NIEUW
```

### Stap 3: Restart Web Server

```bash
# Stop server (Ctrl+C)
# Start opnieuw
python run_web.py
```

### Stap 4: Test Indeed Scrape

1. Ga naar **Source: Indeed → Search Queries**
2. Klik "Run" bij je query
3. Monitor in **Source: Indeed → Scrape Runs**
4. Status zou nu "completed" moeten zijn

## Verificatie

Check of de setting is geladen:

```python
from config.settings import settings

print(f"LinkedIn Dataset ID: {settings.brightdata_dataset_id}")
print(f"Indeed Dataset ID: {settings.brightdata_indeed_dataset_id}")
```

**Verwacht output:**
```
LinkedIn Dataset ID: gd_lpfll7v5hcqtkxl6l
Indeed Dataset ID: gd_your_indeed_dataset_id_here
```

## Alternatief: Gebruik Dezelfde Dataset ID

Als je **geen aparte Indeed dataset** hebt, kun je tijdelijk dezelfde ID gebruiken als LinkedIn:

```bash
# In .env
BRIGHTDATA_INDEED_DATASET_ID=gd_lpfll7v5hcqtkxl6l
```

⚠️ **Let op:** Dit werkt alleen als je Bright Data dataset zowel LinkedIn als Indeed ondersteunt.

## Troubleshooting

### Error: "Invalid dataset_id"

- Check of de Dataset ID correct is gekopieerd
- Verify dat je toegang hebt tot de Indeed dataset in Bright Data
- Check of je API token de juiste permissions heeft

### Error: "Quota exceeded"

- Check je Bright Data quota
- Wacht tot quota reset (meestal dagelijks)
- Upgrade je Bright Data plan indien nodig

### Server start niet

Check of `.env` file correct is:
```bash
cat .env | grep INDEED
```

Moet tonen:
```
BRIGHTDATA_INDEED_DATASET_ID=gd_xxxxxxxxxx
```

## Na Setup

✅ Indeed scrapes zouden nu moeten werken  
✅ Jobs verschijnen in **Fact Data → Jobs** met groene "Indeed" badge  
✅ Zelfde enrichment pipeline als LinkedIn jobs

## Kosten

Indeed scrapes tellen mee voor je Bright Data quota:
- Elke job = 1 API call
- Check je usage in Bright Data dashboard
- Monitor quota in applicatie

🎉 **Indeed is nu klaar voor gebruik!**
