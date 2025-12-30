# Tech Stack Standardization Analysis & Solutions

**Datum:** 4 december 2025  
**Probleem:** Inconsistente naming en duplicaten in tech stack data

---

## 📊 Huidige Situatie

### Database Structuur

**Tabellen:**
- `programming_languages` - Programmeertalen (Python, SQL, DAX, etc.)
- `ecosystems` - Tools, frameworks, platforms (Power BI, Azure, Databricks, etc.)
- `job_programming_languages` - Junction table (jobs ↔ languages)
- `job_ecosystems` - Junction table (jobs ↔ ecosystems)

**Belangrijke Kolommen:**
- `name` (TEXT, UNIQUE) - Canonical name voor matching
- `display_name` (TEXT) - User-editable display name voor frontend
- `logo_url` / `logo_data` - Logo opslag
- `category` - Categorisatie
- `relevance_score` - AI-scored relevantie (0-100)
- `is_active` - Soft deletion

**View:**
```sql
CREATE VIEW tech_stack_lookup AS
  SELECT name, display_name, logo_url, category, 'language' AS type
  FROM programming_languages WHERE is_active = TRUE
  UNION ALL
  SELECT name, display_name, logo_url, category, 'ecosystem' AS type
  FROM ecosystems WHERE is_active = TRUE;
```

### Huidige Data Flow

```
Job Description (raw text)
    ↓
OpenAI Responses API (Prompt v24)
    ↓
LLM Output: {must_have_languages, nice_to_have_languages, must_have_ecosystems, nice_to_have_ecosystems}
    ↓
tech_stack_processor.py
    ↓
Voor elke skill:
  - Lookup by exact name match (case-sensitive)
  - Als niet gevonden: INSERT nieuwe entry met name=display_name
  - Assign to job via junction table
```

### 🔴 Geïdentificeerde Problemen

#### 1. **Duplicaten Across Tables** (32 items)
Dezelfde tech komt voor in BEIDE `programming_languages` EN `ecosystems`:

```
.NET, Alteryx, Angular, Bash, DAX, Databricks, Excel, 
Groovy, Hive, Java, JavaScript, Oracle, Power BI, 
Power Query, PowerShell, PySpark, Python, R, React, 
SAS, SQL, Spark, Terraform, dbt, etc.
```

**Impact:** Frontend toont dezelfde skill 2x in filters/cards

#### 2. **Naming Inconsistenties** 
Power BI varianten:
```
- Power BI
- Microsoft Power BI
- Power BI Service
- PowerBI
```

Andere voorbeelden:
```
- .NET vs .NET Core vs .NET C#
- Spark vs Apache Spark vs PySpark
- dbt vs dbt (data build tool)
```

#### 3. **LLM Output Variabiliteit**
De LLM genereert inconsistente namen:
- "MS PowerBI" vs "Microsoft Power BI" vs "Power BI"
- "PostgreSQL" vs "Postgres" vs "postgres"
- Geen standaardisatie in prompt

#### 4. **Geen Alias Mapping**
Database heeft GEEN alias/synonym tabel voor normalisatie

---

## 🎯 Oplossingsrichtingen

### **Optie 1: Alias Mapping Table (AANBEVOLEN)**

#### Beschrijving
Nieuwe tabel `tech_stack_aliases` die varianten mapped naar canonical entries.

#### Database Schema
```sql
CREATE TABLE tech_stack_aliases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alias TEXT NOT NULL UNIQUE,  -- Variant name (e.g., "PowerBI", "MS Power BI")
    canonical_name TEXT NOT NULL,  -- Canonical name (e.g., "Power BI")
    type TEXT NOT NULL CHECK (type IN ('language', 'ecosystem')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast lookups
CREATE INDEX idx_aliases_alias_lower ON tech_stack_aliases(LOWER(alias));
CREATE INDEX idx_aliases_canonical ON tech_stack_aliases(canonical_name, type);

-- Foreign key to ensure canonical name exists
-- (Optional, kan ook zonder voor flexibiliteit)
```

#### Voorbeeld Data
```sql
INSERT INTO tech_stack_aliases (alias, canonical_name, type) VALUES
    ('PowerBI', 'Power BI', 'ecosystem'),
    ('MS Power BI', 'Power BI', 'ecosystem'),
    ('Microsoft Power BI', 'Power BI', 'ecosystem'),
    ('Power BI Service', 'Power BI', 'ecosystem'),
    ('power bi', 'Power BI', 'ecosystem'),
    
    ('Postgres', 'PostgreSQL', 'ecosystem'),
    ('postgres', 'PostgreSQL', 'ecosystem'),
    ('Postgresql', 'PostgreSQL', 'ecosystem'),
    
    ('Apache Spark', 'Spark', 'ecosystem'),
    ('apache spark', 'Spark', 'ecosystem'),
    
    -- etc.
;
```

#### Code Aanpassingen
**In `tech_stack_processor.py`:**
```python
def _normalize_tech_name(name: str, type: str) -> str:
    """
    Normalize tech stack name using alias mapping.
    
    Args:
        name: Raw name from LLM
        type: 'language' or 'ecosystem'
    
    Returns:
        Canonical name
    """
    name = name.strip()
    
    # Try exact match in aliases (case-insensitive)
    alias_result = db.get_tech_alias(name, type)
    if alias_result:
        return alias_result['canonical_name']
    
    # Fallback: return as-is
    return name

def _process_programming_language(job_id: UUID, language_name: str, requirement_level: str):
    # Normalize BEFORE lookup
    normalized_name = _normalize_tech_name(language_name, 'language')
    
    # Rest of logic stays same, but uses normalized_name
    existing = db.get_programming_language_by_name(normalized_name)
    # ...
```

**Nieuwe DB methods:**
```python
def get_tech_alias(self, alias: str, type: str) -> Optional[Dict]:
    """Get canonical name for an alias."""
    result = self.client.table("tech_stack_aliases")\
        .select("*")\
        .ilike("alias", alias)\
        .eq("type", type)\
        .maybe_single()\
        .execute()
    return result.data if result else None
```

#### ✅ Voordelen
- **Eenvoudig te implementeren** - Geen complexe logica
- **Flexibel** - Nieuwe aliases toevoegen zonder code changes
- **Transparant** - Duidelijk welke varianten naar welke canonical name mappen
- **Backward compatible** - Bestaande data blijft werken
- **Beheerbaar** - Admin UI kan aliases beheren
- **Performant** - Indexed lookups zijn snel

#### ❌ Nadelen
- **Handmatig onderhoud** - Aliases moeten toegevoegd worden
- **Initiële setup** - Bestaande duplicaten moeten opgeschoond worden
- **Niet automatisch** - Nieuwe varianten worden niet automatisch gedetecteerd

#### Implementatie Effort
- **Database:** 1 migration (30 min)
- **Code:** 2-3 functions aanpassen (1 uur)
- **Data cleanup:** Script voor bestaande duplicaten (2-3 uur)
- **Testing:** 1-2 uur
- **Totaal: ~1 dag**

---

### **Optie 2: LLM-Based Normalization (Real-time)**

#### Beschrijving
Gebruik een LLM call om tech stack namen te normaliseren tijdens ingestion.

#### Implementatie
```python
def normalize_with_llm(tech_names: List[str]) -> Dict[str, str]:
    """
    Normalize tech stack names using LLM.
    
    Returns: {original_name: normalized_name}
    """
    prompt = f"""
    Normalize these technology names to their canonical form:
    {json.dumps(tech_names)}
    
    Rules:
    - Use official product names (e.g., "Microsoft Power BI" → "Power BI")
    - Remove vendor prefixes unless essential (e.g., "MS SQL Server" → "SQL Server")
    - Use consistent casing (e.g., "powerbi" → "Power BI")
    - Return JSON: {{"original": "normalized", ...}}
    """
    
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    
    return json.loads(response.choices[0].message.content)

# In tech_stack_processor.py
def process_tech_stack_for_job(job_id: UUID, enrichment_data: Dict):
    all_languages = enrichment_data.get("must_have_languages", []) + \
                    enrichment_data.get("nice_to_have_languages", [])
    all_ecosystems = enrichment_data.get("must_have_ecosystems", []) + \
                     enrichment_data.get("nice_to_have_ecosystems", [])
    
    # Normalize in batch
    normalized_langs = normalize_with_llm(all_languages)
    normalized_ecos = normalize_with_llm(all_ecosystems)
    
    # Process with normalized names
    for original, normalized in normalized_langs.items():
        # Use normalized name for lookup/insert
        ...
```

#### ✅ Voordelen
- **Automatisch** - Geen handmatig onderhoud van aliases
- **Intelligent** - LLM begrijpt context en varianten
- **Adaptief** - Werkt met nieuwe tech zonder updates

#### ❌ Nadelen
- **Extra LLM calls** - Kosten en latency per job
- **Niet deterministisch** - LLM kan inconsistent zijn
- **Afhankelijk van LLM** - Geen controle over normalisatie logica
- **Moeilijk te debuggen** - Waarom werd X naar Y gemapped?
- **Rate limits** - Extra API calls kunnen limits raken

#### Implementatie Effort
- **Code:** Normalization function + integratie (2-3 uur)
- **Testing:** Uitgebreid testen van edge cases (3-4 uur)
- **Monitoring:** Error handling en logging (1-2 uur)
- **Totaal: ~1-1.5 dag**

---

### **Optie 3: Fuzzy Matching + Similarity**

#### Beschrijving
Gebruik string similarity (Levenshtein distance, trigrams) om varianten te detecteren.

#### Implementatie
```python
from difflib import SequenceMatcher
import re

def find_similar_tech(name: str, type: str, threshold: float = 0.85) -> Optional[str]:
    """
    Find similar tech stack entry using fuzzy matching.
    
    Args:
        name: Input name
        type: 'language' or 'ecosystem'
        threshold: Similarity threshold (0-1)
    
    Returns:
        Canonical name if similar match found, else None
    """
    # Normalize for comparison
    normalized_input = re.sub(r'[^a-z0-9]', '', name.lower())
    
    # Get all existing entries
    if type == 'language':
        existing = db.get_all_programming_languages()
    else:
        existing = db.get_all_ecosystems()
    
    best_match = None
    best_score = 0
    
    for entry in existing:
        normalized_existing = re.sub(r'[^a-z0-9]', '', entry['name'].lower())
        
        # Calculate similarity
        score = SequenceMatcher(None, normalized_input, normalized_existing).ratio()
        
        if score > best_score and score >= threshold:
            best_score = score
            best_match = entry['name']
    
    return best_match

# In tech_stack_processor.py
def _process_programming_language(job_id: UUID, language_name: str, requirement_level: str):
    language_name = language_name.strip()
    
    # Try exact match first
    existing = db.get_programming_language_by_name(language_name)
    
    if not existing:
        # Try fuzzy match
        similar = find_similar_tech(language_name, 'language')
        if similar:
            logger.info(f"Fuzzy matched '{language_name}' → '{similar}'")
            existing = db.get_programming_language_by_name(similar)
    
    # Rest of logic...
```

#### ✅ Voordelen
- **Automatische detectie** - Geen handmatige alias lijst
- **Geen extra API calls** - Alles lokaal
- **Deterministisch** - Zelfde input → zelfde output

#### ❌ Nadelen
- **False positives** - "Java" vs "JavaScript" (similarity 0.66)
- **Performance** - O(n) vergelijking bij elke lookup
- **Moeilijk te tunen** - Threshold is arbitrair
- **Geen context** - "Spark" vs "Apache Spark" vs "PySpark"
- **Niet perfect** - "PowerBI" vs "Power BI" werkt, maar "MS Power BI" vs "Power BI" niet

#### Implementatie Effort
- **Code:** Fuzzy matching logic (2-3 uur)
- **Testing:** Uitgebreid testen + threshold tuning (4-5 uur)
- **Performance optimization:** Caching, indexing (2-3 uur)
- **Totaal: ~1.5-2 dagen**

---

### **Optie 4: Hybrid Approach (Alias + LLM Fallback)**

#### Beschrijving
Combineer Optie 1 en 2: gebruik alias table eerst, LLM als fallback voor onbekende varianten.

#### Flow
```
Input: "MS PowerBI"
    ↓
1. Check alias table → Found: "Power BI" ✅
    ↓
Use canonical name

Input: "Some New Tool 2025"
    ↓
1. Check alias table → Not found
    ↓
2. LLM normalization → "Some New Tool"
    ↓
3. Check if exists → Not found
    ↓
4. Create new entry + add alias mapping
```

#### ✅ Voordelen
- **Best of both worlds** - Snelheid van aliases + intelligentie van LLM
- **Zelflerend** - Nieuwe aliases worden automatisch toegevoegd
- **Fallback** - Altijd een oplossing

#### ❌ Nadelen
- **Complexer** - Meer moving parts
- **LLM kosten** - Voor onbekende varianten
- **Meer code** - Beide systemen onderhouden

#### Implementatie Effort
- **Totaal: ~2-3 dagen** (combinatie van Optie 1 + 2)

---

### **Optie 5: Prompt Engineering (Preventief)**

#### Beschrijving
Verbeter de LLM prompt om gestandaardiseerde output te forceren.

#### Implementatie
Update OpenAI Responses prompt (v25):
```
Extract tech stack from job description.

IMPORTANT - Use these EXACT canonical names:
- Programming Languages: Python, SQL, R, Java, JavaScript, TypeScript, C#, Scala, Go, Rust, DAX, M, MDX
- Cloud: Azure, AWS, GCP (NOT "Microsoft Azure", "Amazon AWS", etc.)
- BI Tools: Power BI, Tableau, Looker (NOT "PowerBI", "MS Power BI", etc.)
- Data Platforms: Databricks, Snowflake, BigQuery, Redshift, Synapse
- Tools: dbt, Airflow, Kafka, Spark, Docker, Kubernetes, Terraform

Rules:
1. Use official product names WITHOUT vendor prefix (e.g., "Power BI" not "Microsoft Power BI")
2. Use consistent casing (e.g., "Power BI" not "powerbi")
3. If unsure, use the most common industry name

Output JSON:
{
  "must_have_languages": ["Python", "SQL"],
  "nice_to_have_languages": ["R"],
  "must_have_ecosystems": ["Power BI", "Azure"],
  "nice_to_have_ecosystems": ["Databricks"]
}
```

#### ✅ Voordelen
- **Upstream fix** - Probleem oplossen bij de bron
- **Geen extra code** - Alleen prompt update
- **Geen extra kosten** - Zelfde LLM call

#### ❌ Nadelen
- **Niet 100% betrouwbaar** - LLM kan nog steeds afwijken
- **Beperkte lijst** - Kan niet alle tech bevatten
- **Maintenance** - Prompt moet up-to-date blijven
- **Lost bestaande data niet op** - Alleen nieuwe jobs

#### Implementatie Effort
- **Prompt update:** 1-2 uur
- **Testing:** 2-3 uur
- **Totaal: ~0.5 dag**

---

## 🏆 Aanbeveling: **Optie 1 + Optie 5 (Alias Table + Prompt Engineering)**

### Waarom?

1. **Optie 5 (Prompt Engineering)** - Preventief
   - Vermindert nieuwe inconsistenties
   - Geen extra kosten
   - Snel te implementeren

2. **Optie 1 (Alias Table)** - Curatief
   - Lost bestaande duplicaten op
   - Flexibel en transparant
   - Eenvoudig te beheren
   - Backward compatible

### Implementatie Roadmap

#### **Fase 1: Prompt Engineering (Week 1)**
- [ ] Update OpenAI Responses prompt naar v25
- [ ] Test met 50-100 jobs
- [ ] Monitor output kwaliteit
- [ ] **Effort: 0.5 dag**

#### **Fase 2: Alias Table (Week 1-2)**
- [ ] Create migration `078_add_tech_stack_aliases.sql`
- [ ] Populate initial aliases (top 100 varianten)
- [ ] Update `tech_stack_processor.py` met normalization
- [ ] Add DB methods voor alias lookup
- [ ] **Effort: 1 dag**

#### **Fase 3: Data Cleanup (Week 2)**
- [ ] Script: Identify duplicates across tables
- [ ] Script: Merge duplicates (keep best entry)
- [ ] Script: Update job assignments
- [ ] Verify data integrity
- [ ] **Effort: 1 dag**

#### **Fase 4: Admin UI (Week 3 - Optional)**
- [ ] Admin page voor alias management
- [ ] Bulk import aliases
- [ ] Duplicate detection tool
- [ ] **Effort: 2-3 dagen**

### Totale Effort
- **Minimaal (Fase 1-3):** 2.5 dagen
- **Met Admin UI (Fase 1-4):** 4.5-5.5 dagen

---

## 📋 Concrete Volgende Stappen

### Stap 1: Beslissing
- [ ] Akkoord op gekozen oplossing?
- [ ] Budget/tijd beschikbaar?

### Stap 2: Quick Win (Prompt Engineering)
```bash
# Update prompt in OpenAI dashboard
# Test met sample jobs
# Deploy naar productie
```

### Stap 3: Alias Table Implementation
```bash
# Create migration
# Populate aliases
# Update code
# Test
# Deploy
```

### Stap 4: Data Cleanup
```bash
# Run duplicate detection
# Review merge plan
# Execute cleanup
# Verify results
```

---

## 🔍 Aanvullende Overwegingen

### Performance Impact
- Alias lookup: **+5-10ms per tech item** (negligible)
- LLM normalization: **+500-1000ms per job** (significant)
- Fuzzy matching: **+50-100ms per tech item** (moderate)

### Maintenance
- Alias table: **~1 uur/maand** (nieuwe aliases toevoegen)
- Prompt engineering: **~2 uur/kwartaal** (prompt updates)
- LLM normalization: **Minimal** (automatisch)

### Schaalbaarheid
- Alias table: **Excellent** (indexed lookups)
- LLM normalization: **Poor** (rate limits, kosten)
- Fuzzy matching: **Moderate** (O(n) complexity)

---

## 📊 Vergelijkingstabel

| Criterium | Optie 1 (Alias) | Optie 2 (LLM) | Optie 3 (Fuzzy) | Optie 4 (Hybrid) | Optie 5 (Prompt) |
|-----------|----------------|---------------|-----------------|------------------|------------------|
| **Implementatie** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Accuraatheid** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Performance** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Onderhoud** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Kosten** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Flexibiliteit** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |

**Winnaar: Optie 1 (Alias Table) + Optie 5 (Prompt Engineering)**

---

## 💡 Extra Ideeën

### 1. Admin Dashboard Feature
- Duplicate detection tool
- Alias management UI
- Bulk merge tool
- Preview impact before merge

### 2. Monitoring & Alerts
- Alert bij nieuwe tech stack items (mogelijk duplicaat)
- Dashboard met top onbekende varianten
- Weekly report met normalization stats

### 3. Community Sourced Aliases
- Frontend: "Is dit dezelfde tool?" suggestie
- Crowdsource alias mapping van recruiters
- Auto-learn van user corrections

---

**Wil je dat ik begin met de implementatie van de aanbevolen oplossing?**
