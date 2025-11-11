# UI Update: Hiring Model Display

## Probleem

Het `hiring_model` veld was niet zichtbaar in de UI, ook al bestond het al in de database en was Abbott al enriched met v15.

## Oplossing

### 1. UI Template Update ✅

**Bestand:** `web/templates/companies.html`

Toegevoegd: Nieuwe "Hiring Model" sectie tussen "Company Size Classification" en "AI Enriched Information"

**Features:**
- 🎨 **Badge met kleur coding:**
  - 🟣 Purple voor "Recruitment"
  - 🟢 Green voor "Direct"
  - ⚪ Gray voor "Unknown"

- 🌍 **Multilingual labels:**
  - 🇬🇧 English
  - 🇳🇱 Dutch
  - 🇫🇷 French

- 💡 **Uitleg tooltip:**
  - Recruitment: "This company provides recruitment/staffing services"
  - Direct: "This company hires directly for its own organization"
  - Unknown: "Hiring model could not be determined"

### 2. API ✅

**Geen wijzigingen nodig!**

De API gebruikt al `company_master_data(*)` wat automatisch alle velden meestuurt, inclusief:
- `hiring_model`
- `hiring_model_en`
- `hiring_model_nl`
- `hiring_model_fr`

## UI Preview

### Abbott (Direct Hiring)

```
┌─────────────────────────────────────────────┐
│ 💼 Hiring Model                             │
├─────────────────────────────────────────────┤
│ ┌─────────┐                                 │
│ │ Direct  │ (green badge)                   │
│ └─────────┘                                 │
│                                             │
│ 🇬🇧 Direct                                  │
│ 🇳🇱 Direct                                  │
│ 🇫🇷 Direct                                  │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ 🏭 This company hires directly for its  │ │
│ │    own organization                     │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### Randstad (Recruitment)

```
┌─────────────────────────────────────────────┐
│ 💼 Hiring Model                             │
├─────────────────────────────────────────────┤
│ ┌─────────────┐                             │
│ │ Recruitment │ (purple badge)              │
│ └─────────────┘                             │
│                                             │
│ 🇬🇧 Recruitment                             │
│ 🇳🇱 Recruitment                             │
│ 🇫🇷 Recrutement                             │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │ 🏢 This company provides recruitment/   │ │
│ │    staffing services (interim,          │ │
│ │    headhunting, RPO)                    │ │
│ └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

## Testing

### 1. Restart Web Server

```bash
# Stop current server (Ctrl+C)
# Start again
python run_web.py
```

### 2. Open Companies Page

```
http://localhost:8000/companies
```

### 3. View Abbott Details

1. Search for "Abbott"
2. Click "View Details"
3. Scroll to "Hiring Model" section
4. Should show green "Direct" badge

### 4. Test with Recruitment Company

1. Search for "Randstad" or "Manpower"
2. Click "View Details"
3. Should show purple "Recruitment" badge

## Visibility Logic

De sectie wordt alleen getoond als `hiring_model` bestaat:

```html
<div x-show="viewingCompany.company_master_data?.hiring_model" ...>
```

**Dit betekent:**
- ✅ Companies met v15 enrichment: sectie is zichtbaar
- ❌ Companies met v14 of ouder: sectie is verborgen
- ❌ Companies zonder enrichment: sectie is verborgen

## Backward Compatibility

### Oude Enrichments (v14)

Companies enriched met v14 hebben `hiring_model = NULL`:
- Sectie wordt niet getoond (x-show conditie)
- Geen errors in UI
- Re-enrich met v15 om veld te vullen

### Re-enrichment

```python
from ingestion.company_enrichment import enrich_company

# Re-enrich company met v15
result = enrich_company(company_id, company_name)
```

## Checklist

- [x] UI template aangepast
- [x] Badge styling toegevoegd
- [x] Multilingual labels
- [x] Uitleg tooltips
- [x] API check (geen wijzigingen nodig)
- [ ] Web server restart
- [ ] Test met Abbott (direct)
- [ ] Test met Randstad (recruitment)

## Troubleshooting

### Sectie niet zichtbaar

**Check 1: Database**
```python
python check_abbott_hiring_model.py
```

Verwacht: `hiring_model: 'direct'`

**Check 2: Browser Cache**
```
Hard refresh: Cmd+Shift+R (Mac) of Ctrl+Shift+R (Windows)
```

**Check 3: Web Server**
```bash
# Restart server
pkill -f "run_web.py"
python run_web.py
```

### Badge heeft geen kleur

Check Alpine.js conditie:
```javascript
:class="{
    'bg-purple-100 text-purple-800': ... === 'recruitment',
    'bg-green-100 text-green-800': ... === 'direct',
    'bg-gray-100 text-gray-800': ... === 'unknown',
}"
```

Waarde moet exact matchen: `'recruitment'`, `'direct'`, of `'unknown'`

### Multilingual labels ontbreken

Check database velden:
```sql
SELECT hiring_model_en, hiring_model_nl, hiring_model_fr
FROM company_master_data
WHERE company_id = 'abbott-id';
```

Alle drie moeten gevuld zijn bij v15 enrichment.

## Future Enhancements

### 1. Filter in Companies List

```html
<select id="hiringModelFilter">
  <option value="">All Companies</option>
  <option value="direct">Direct Hiring Only</option>
  <option value="recruitment">Recruitment Agencies Only</option>
</select>
```

### 2. Badge in Company List

Toon hiring_model badge direct in de companies lijst (niet alleen in details)

### 3. Job Filtering

Filter jobs op company hiring_model:
```
"Hide jobs from recruitment agencies" checkbox
```

### 4. Analytics

Dashboard met:
- % recruitment vs direct companies
- Jobs per hiring model
- Top recruitment agencies
