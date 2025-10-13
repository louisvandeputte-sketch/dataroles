# 🗺️ Location Filtering Issue - Analysis

## ❌ Probleem

**Query**: "powerbi" in "Gent"
**Verwacht**: Jobs uit Gent, België
**Actueel**: Jobs uit Arnhem, Apeldoorn, Oss (Nederland)

### Resultaten Breakdown
```
Total jobs: 33
Jobs in Gent: 0

Top locations:
- Arnhem, Gelderland, Netherlands: 13 jobs
- Apeldoorn, Gelderland, Netherlands: 3 jobs
- Oss, North Brabant, Netherlands: 3 jobs
- Gelderland, Netherlands: 3 jobs
```

## 🔍 Root Cause Analysis

### Wat Wordt Gestuurd naar Bright Data
```json
{
  "input": [{
    "keyword": "powerbi",
    "location": "Gent",  // ← PROBLEEM: Te vaag!
    "time_range": "Past week",
    "country": "",
    "location_radius": ""
  }]
}
```

### Wat LinkedIn Doet
LinkedIn interpreteert "Gent" als:
1. ❌ **Niet specifiek genoeg** - welk land?
2. ❌ **Mogelijk verward** met Nederlandse steden
3. ❌ **Geen resultaten** in Gent → toont nabije locaties
4. ❌ **Default gedrag**: Toont jobs uit regio (Gelderland, NL)

## 🎯 Oplossingen

### Optie A: Gebruik Volledige Locatie String (Aanbevolen)

**Probleem**: "Gent" is te vaag
**Oplossing**: "Gent, Belgium" of "Ghent, Belgium"

**Code change**:
```python
# In trigger_collection
payload = {
    "input": [{
        "keyword": keyword,
        "location": location,  # User input: "Gent"
        "country": "BE",  # ← ADD: Explicit country code
        ...
    }]
}
```

**Of beter**: Normalize location input
```python
def normalize_location(location: str) -> tuple[str, str]:
    """
    Normalize location to (location, country_code).
    
    Examples:
        "Gent" → ("Ghent", "BE")
        "Antwerpen" → ("Antwerp", "BE")
        "Amsterdam" → ("Amsterdam", "NL")
    """
    # Belgium cities
    belgium_cities = {
        "gent": ("Ghent", "BE"),
        "antwerpen": ("Antwerp", "BE"),
        "brussel": ("Brussels", "BE"),
        "brugge": ("Bruges", "BE"),
        "leuven": ("Leuven", "BE"),
    }
    
    location_lower = location.lower().strip()
    
    if location_lower in belgium_cities:
        return belgium_cities[location_lower]
    
    # Default: assume user knows what they're doing
    return (location, "")
```

### Optie B: Laat User Country Kiezen

**UI change**: Add country dropdown in query form
```html
<select name="country">
    <option value="">Any Country</option>
    <option value="BE">Belgium</option>
    <option value="NL">Netherlands</option>
    <option value="FR">France</option>
    <option value="DE">Germany</option>
</select>
```

### Optie C: Gebruik LinkedIn's Locatie Format

LinkedIn verwacht vaak:
- "Ghent, Belgium" (Engels)
- "Gent, België" (Nederlands)
- "Gand, Belgique" (Frans)

**Aanbeveling**: Gebruik Engels voor consistentie
```
"Gent" → "Ghent, Belgium"
"Antwerpen" → "Antwerp, Belgium"
"Brussel" → "Brussels, Belgium"
```

## 🧪 Test Cases

### Test 1: Huidige Situatie
```
Input: location="Gent"
Bright Data: {"location": "Gent", "country": ""}
LinkedIn: Interpreteert als Nederland? → Arnhem jobs
Result: ❌ 0 Gent jobs, 33 Nederland jobs
```

### Test 2: Met Country Code
```
Input: location="Gent"
Bright Data: {"location": "Gent", "country": "BE"}
LinkedIn: Zoekt in België
Result: ✅ Gent jobs (als beschikbaar)
```

### Test 3: Met Volledige String
```
Input: location="Ghent, Belgium"
Bright Data: {"location": "Ghent, Belgium", "country": ""}
LinkedIn: Duidelijk België
Result: ✅ Gent jobs
```

### Test 4: Geen Jobs Beschikbaar
```
Input: location="Ghent, Belgium", keyword="powerbi"
LinkedIn: Geen Power BI jobs in Gent
Result: ⚠️ Mogelijk nabije locaties (Brussel, Antwerpen)
```

## 📊 LinkedIn Gedrag

### Waarom Arnhem?
LinkedIn's algoritme:
1. Zoekt naar "powerbi" in "Gent"
2. Vindt weinig/geen resultaten
3. Expandeert zoekgebied automatisch
4. Toont jobs uit "nabije" locaties
5. **Probleem**: "Nabij" wordt verkeerd geïnterpreteerd

### LinkedIn's Location Matching
```
User input: "Gent"
LinkedIn denkt:
- Is dit Gent, België?
- Is dit Gent, Nederland? (bestaat niet, maar lijkt op Gelderland?)
- Geen resultaten → toon nabije jobs
- "Nabij" = Arnhem, Apeldoorn (Nederland)
```

## 🔧 Aanbevolen Fix

### Stap 1: Add Country Field to Query Model

```python
# models/query.py
class SearchQuery(BaseModel):
    search_query: str
    location_query: str
    country_code: Optional[str] = "BE"  # Default to Belgium
    lookback_days: int = 7
```

### Stap 2: Update Bright Data Payload

```python
# clients/brightdata_linkedin.py
payload = {
    "input": [{
        "keyword": keyword,
        "location": location,
        "country": country_code or "",  # Use provided country
        "time_range": time_range,
        ...
    }]
}
```

### Stap 3: Update UI

```html
<!-- web/templates/queries.html -->
<div>
    <label>Location</label>
    <input name="location" value="Gent">
</div>
<div>
    <label>Country</label>
    <select name="country">
        <option value="BE" selected>Belgium</option>
        <option value="NL">Netherlands</option>
        <option value="FR">France</option>
        <option value="DE">Germany</option>
        <option value="">Any</option>
    </select>
</div>
```

### Stap 4: Or Use Smart Defaults

```python
# Auto-detect Belgium cities
BELGIUM_CITIES = ["gent", "antwerpen", "brussel", "brugge", "leuven", "mechelen", "aalst", "hasselt", "genk", "oostende"]

def get_country_for_location(location: str) -> str:
    """Auto-detect country based on city name."""
    if location.lower() in BELGIUM_CITIES:
        return "BE"
    return ""  # Let LinkedIn decide
```

## 🎯 Quick Fix (Minimal Change)

**Simpelste oplossing**: Laat users "Ghent, Belgium" typen in plaats van "Gent"

**UI hint**:
```html
<input name="location" 
       placeholder="e.g., Ghent, Belgium or Amsterdam, Netherlands">
```

## ✅ Verificatie

Na fix, test met:
```
Query: "powerbi"
Location: "Ghent, Belgium" (of country="BE")
Expected: Jobs uit Gent/België
```

Check:
```python
jobs = await client.download_results(snapshot_id)
locations = [j.get('job_location') for j in jobs]
belgium_jobs = [l for l in locations if 'Belgium' in l or 'België' in l]
print(f"Belgium jobs: {len(belgium_jobs)}/{len(jobs)}")
```

---

**Conclusie**: LinkedIn interpreteert "Gent" verkeerd. Gebruik "Ghent, Belgium" of voeg country code toe!
