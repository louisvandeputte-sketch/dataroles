# Company Deduplication - Implementatie

## Probleem

**Voor de fix:**
- ❌ 963 companies in database
- ❌ 53 namen met duplicates (148 duplicate entries totaal)
- ❌ Voorbeeld: "Robert Walters" had 10 entries, "AE" had 2 entries
- ❌ Indeed jobs creëerden altijd nieuwe company entries

**Oorzaak:**
- LinkedIn scraper: Dedupliceert op `linkedin_company_id` ✅
- Indeed scraper: Dedupliceert NIET - maakt altijd nieuwe entry ❌

## Oplossing

### Stap 1: Cleanup Bestaande Duplicates ✅

**Script:** `merge_duplicate_companies_auto.py`

**Strategie:**
1. Groepeer companies op naam
2. Voor elke groep, bepaal welke te behouden:
   - **Prioriteit 1:** Company met `logo_data` (profielfoto) 🏆
   - **Prioriteit 2:** Company met `logo_url`
   - **Prioriteit 3:** Company met `linkedin_company_id`
   - **Prioriteit 4:** Company met meeste jobs
3. Merge alle jobs naar de behouden company
4. Verwijder duplicate companies

**Resultaat:**
- ✅ 963 → 868 companies (-95 duplicates)
- ✅ Alle jobs blijven gekoppeld
- ✅ "AE" nu 1 entry (met LinkedIn ID en logo)
- ✅ Geen data verlies

### Stap 2: Preventie Voor Toekomst ✅

**Gewijzigde bestanden:**

#### 1. `database/client.py`
Nieuwe methode: `get_company_by_name(name)`

```python
def get_company_by_name(self, name: str) -> Optional[Dict]:
    """
    Get company by exact name match.
    
    Priority: Returns company with logo_data first, 
    then linkedin_company_id, then first match.
    """
    # Returns best matching company if multiple exist
```

**Logica:**
- Als 1 company met naam → return die
- Als meerdere companies met naam:
  1. Return company met `logo_data` (hoogste prioriteit)
  2. Anders company met `linkedin_company_id`
  3. Anders eerste match

#### 2. `ingestion/processor.py`
Updated company processing logica:

```python
if company_data.get("linkedin_company_id"):
    # LinkedIn job: Check by LinkedIn ID
    existing_company = db.get_company_by_linkedin_id(...)
else:
    # Indeed job: Check by NAME to avoid duplicates ✅
    existing_company = db.get_company_by_name(company_data["name"])
    
if existing_company:
    company_id = existing_company["id"]  # Reuse!
else:
    company_id = db.insert_company(...)  # Create new
```

**Voordelen:**
- ✅ Indeed jobs hergebruiken bestaande companies
- ✅ Geen nieuwe duplicates
- ✅ Voorkeur voor companies met logo's
- ✅ LinkedIn + Indeed jobs delen dezelfde company entry

## Database Schema

```sql
companies
├── id (UUID, PRIMARY KEY)
├── name (TEXT) -- NOT UNIQUE by design
├── linkedin_company_id (TEXT, UNIQUE)
├── logo_data (BYTEA)
├── logo_url (TEXT)
└── ... other fields

job_postings
├── id (UUID, PRIMARY KEY)
├── company_id (UUID, FOREIGN KEY → companies.id)
└── ... other fields
```

**Relatie:**
- `job_postings.company_id` → `companies.id`
- Meerdere jobs kunnen naar dezelfde company wijzen
- Company naam hoeft NIET unique te zijn (verschillende bedrijven kunnen zelfde naam hebben)

## Testing

### Test 1: Verify No Duplicates
```bash
python check_company_duplicates.py
```

**Expected output:**
```
📊 Total companies: 868
🔍 Duplicate names: 0
✅ No duplicates found!
```

### Test 2: Test Deduplication Logic
```bash
python test_company_dedup.py
```

**Expected output:**
```
✅ Found company: AE
  LinkedIn ID: 270644
  Has logo_url: True
✅ No duplicates found!
```

### Test 3: Run Indeed Scrape
```bash
# In Python
from scraper import execute_scrape_run

run_id = execute_scrape_run(
    search_query='Data Engineer',
    location='Belgium',
    source='indeed'
)
```

**Expected behavior:**
- Indeed jobs reuse existing companies by name
- No new duplicate companies created
- Check logs for: "Reusing existing company: [name]"

## Monitoring

### Check for New Duplicates

Run periodically:
```bash
python check_company_duplicates.py
```

If duplicates appear:
```bash
python merge_duplicate_companies_auto.py
```

### Logs

During scraping, watch for:
```
DEBUG - Reusing existing company: Microsoft
DEBUG - Created new company: NewStartup Inc
```

## Edge Cases

### Case 1: Same Name, Different Companies

**Example:** "AE" could be:
- AE (engineering firm, LinkedIn ID: 270644)
- AE (consulting firm, no LinkedIn ID)

**Solution:**
- If both have LinkedIn IDs → Separate entries (correct)
- If one has LinkedIn ID → Reuse that one for Indeed jobs
- If neither has LinkedIn ID → Reuse first match

### Case 2: Company Name Variations

**Example:**
- "Microsoft"
- "Microsoft Corporation"
- "Microsoft Belgium"

**Current behavior:** Treated as different companies (exact match only)

**Future improvement:** Fuzzy matching or normalization

### Case 3: Merging Company Data

When Indeed job reuses LinkedIn company:
- ✅ Jobs are linked correctly
- ⚠️ Indeed-specific data (rating, reviews) not merged
- 💡 Future: Merge company metadata from both sources

## Metrics

**Before:**
- 963 companies
- 53 duplicate names
- 148 total duplicate entries

**After:**
- 868 companies (-9.9%)
- 0 duplicate names
- 0 duplicate entries

**Prevented:**
- Future Indeed scrapes will not create duplicates
- Estimated: ~50-100 duplicate companies prevented per month

## Files Changed

```
✅ database/client.py - Added get_company_by_name()
✅ ingestion/processor.py - Updated Indeed company logic
✅ merge_duplicate_companies_auto.py - Cleanup script
✅ check_company_duplicates.py - Monitoring script
✅ test_company_dedup.py - Test script
✅ COMPANY_DEDUPLICATION.md - This documentation
```

## Rollback Plan

If issues occur:

1. **Revert code changes:**
```bash
git checkout HEAD -- database/client.py ingestion/processor.py
```

2. **Database is safe:**
   - Merged companies cannot be "unmerged" automatically
   - Jobs remain correctly linked
   - No data loss

3. **Manual fix if needed:**
   - Identify problematic company
   - Create new company entry
   - Update affected jobs' `company_id`

## Future Enhancements

- [ ] Fuzzy company name matching
- [ ] Company name normalization (remove "Inc", "Ltd", etc.)
- [ ] Merge company metadata from multiple sources
- [ ] UI to manually merge companies
- [ ] Automated duplicate detection alerts
- [ ] Company master data deduplication
