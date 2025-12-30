# Company Enrichment Automation

**Status:** ✅ Active  
**Schedule:** Every 10 hours  
**Batch size:** 50 companies per batch  
**Max per run:** 200 companies

---

## 🎯 What It Does

Automatically enriches unenriched companies every 10 hours:
- Fetches company info using OpenAI LLM
- Extracts: sector, description, size, location, hiring model, etc.
- Retries failed companies after 24 hours
- Logs all activity

---

## 📊 Current Status

Check enrichment stats:
```bash
python3 -c "
from ingestion.company_enrichment import get_enrichment_stats
stats = get_enrichment_stats()
print(f\"Enriched: {stats['enriched']}/{stats['total']} ({stats['percentage_enriched']}%)\")
print(f\"Remaining: {stats['unenriched']}\")
"
```

---

## 🚀 Setup (Already Done)

The automation is already set up and running via macOS LaunchAgent:

**LaunchAgent file:** `~/Library/LaunchAgents/com.datarole.company-enrichment.plist`

**Schedule:** Every 10 hours (36000 seconds)

**Runs:**
- Immediately on system boot
- Every 10 hours after that

---

## 🔧 Management

### Check Status
```bash
# Check if scheduler is running
launchctl list | grep datarole

# Should show: com.datarole.company-enrichment
```

### View Logs
```bash
# Latest log
tail -f logs/company_enrichment_stdout.log

# All logs
ls -lh logs/company_enrichment_*.log

# Errors
tail -f logs/company_enrichment_stderr.log
```

### Stop Scheduler
```bash
launchctl unload ~/Library/LaunchAgents/com.datarole.company-enrichment.plist
```

### Start Scheduler
```bash
launchctl load ~/Library/LaunchAgents/com.datarole.company-enrichment.plist
```

### Restart Scheduler
```bash
launchctl unload ~/Library/LaunchAgents/com.datarole.company-enrichment.plist && \
launchctl load ~/Library/LaunchAgents/com.datarole.company-enrichment.plist
```

### Run Manually (Test)
```bash
# Run the enrichment script manually
./scripts/run_company_enrichment.sh

# Or with custom parameters
python3 scripts/auto_enrich_companies.py --batch-size 10 --max-total 50
```

---

## 📋 Script Details

### Main Script
**File:** `scripts/auto_enrich_companies.py`

**Parameters:**
- `--batch-size 50` - Companies per batch (default: 50)
- `--max-total 200` - Max companies per run (default: 200)
- `--no-retries` - Skip retrying failed companies

**Example:**
```bash
python3 scripts/auto_enrich_companies.py --batch-size 25 --max-total 100
```

### Wrapper Script
**File:** `scripts/run_company_enrichment.sh`

Sets up environment and runs the main script:
- Activates virtual environment
- Sets PYTHONPATH
- Loads .env variables
- Runs enrichment
- Cleans up old logs (>30 days)

---

## 🔍 How It Works

1. **Fetch unenriched companies**
   - Companies without `ai_enriched = true`
   - Companies with errors >24h old (auto-retry)

2. **Process in batches**
   - Default: 50 companies per batch
   - 3 second delay between companies (rate limiting)
   - Max 200 companies per run

3. **For each company:**
   - Call OpenAI LLM with company name + URL
   - Extract structured data (sector, size, description, etc.)
   - Save to `company_master_data` table
   - Log success/failure

4. **Retry logic**
   - Failed companies are retried after 24 hours
   - Quota errors automatically retried next run

---

## 📊 What Gets Enriched

For each company, the LLM extracts:

**Company Info:**
- `bedrijfswebsite` - Company website
- `jobspagina` - Careers page URL
- `email_hr` - HR email
- `email_algemeen` - General email
- `locatie_belgie` - Belgian office location

**Descriptions (NL/EN/FR):**
- `bedrijfsomschrijving_nl/en/fr` - Company description

**Sector (NL/EN/FR):**
- `sector_nl/en/fr` - Industry sector

**Size Classification:**
- `size_category` - startup/scaleup/sme/corporate/enterprise
- `aantal_werknemers` - Employee count range
- `size_confidence` - Confidence score
- `size_key_arguments` - Reasoning

**Hiring Model:**
- `hiring_model` - direct/recruitment_agency/both
- `hiring_model_nl/en/fr` - Translations

**Factlets:**
- `weetjes` - 3 interesting facts about the company

---

## 🐛 Troubleshooting

### Scheduler Not Running

**Check if loaded:**
```bash
launchctl list | grep datarole
```

**If not listed, reload:**
```bash
launchctl load ~/Library/LaunchAgents/com.datarole.company-enrichment.plist
```

### No Logs Generated

**Check permissions:**
```bash
ls -la logs/
```

**Create logs directory:**
```bash
mkdir -p logs
```

### OpenAI API Errors

**Check API key:**
```bash
echo $OPENAI_API_KEY
```

**Check .env file:**
```bash
cat .env | grep OPENAI_API_KEY
```

### Rate Limiting

The script includes:
- 3 second delay between companies
- 5 minute timeout per API call
- Automatic retry after 24h for quota errors

If you hit rate limits, reduce batch size:
```bash
python3 scripts/auto_enrich_companies.py --batch-size 25
```

---

## 📈 Performance

**Typical run (50 companies):**
- Duration: ~3-5 minutes
- API calls: 50
- Cost: ~$0.50-1.00 (depends on model)

**Daily enrichment (3 runs):**
- Companies: ~150
- Duration: ~10-15 minutes total
- Cost: ~$1.50-3.00

**Full enrichment (924 companies):**
- Runs needed: ~5-6 (at 200/run)
- Duration: ~30-50 minutes total
- Cost: ~$10-20

---

## ⚙️ Configuration

### Change Schedule

Edit the plist file:
```bash
nano ~/Library/LaunchAgents/com.datarole.company-enrichment.plist
```

Change `StartInterval`:
```xml
<key>StartInterval</key>
<integer>36000</integer>  <!-- 10 hours = 36000 seconds -->
```

Common intervals:
- 1 hour: 3600
- 6 hours: 21600
- 12 hours: 43200
- 24 hours: 86400

Then reload:
```bash
launchctl unload ~/Library/LaunchAgents/com.datarole.company-enrichment.plist && \
launchctl load ~/Library/LaunchAgents/com.datarole.company-enrichment.plist
```

### Change Batch Size

Edit wrapper script:
```bash
nano scripts/run_company_enrichment.sh
```

Change the python command:
```bash
python3 "$SCRIPT_PATH" --batch-size 100 --max-total 500
```

---

## 📊 Monitoring

### Check Last Run
```bash
# View latest log
tail -20 logs/company_enrichment_stdout.log
```

### Check Success Rate
```bash
# Count successful vs failed
grep "✅" logs/company_enrichment_stdout.log | wc -l
grep "❌" logs/company_enrichment_stdout.log | wc -l
```

### Check Progress
```bash
# Get current stats
python3 -c "
from ingestion.company_enrichment import get_enrichment_stats
stats = get_enrichment_stats()
print(f'Progress: {stats[\"enriched\"]}/{stats[\"total\"]} ({stats[\"percentage_enriched\"]}%)')
"
```

---

## 🎉 Success!

The automation is now running and will enrich companies every 10 hours automatically!

**Next enrichment:** Check logs in `logs/company_enrichment_*.log`

**Current status:** Run `launchctl list | grep datarole` to verify it's active.
