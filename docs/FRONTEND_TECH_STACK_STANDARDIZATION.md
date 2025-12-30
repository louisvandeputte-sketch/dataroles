# Tech Stack Standardization - Frontend Developer Guide

**Datum:** 4 december 2025  
**Status:** ✅ Geïmplementeerd  
**Doel:** Gestandaardiseerde tech stack data voor dashboard en filters

---

## 📋 Overzicht

De tech stack data (`programming_languages` en `ecosystems`) is gestandaardiseerd om inconsistenties en duplicaten op te lossen. Dit document beschrijft wat er veranderd is en hoe je de data moet gebruiken in de frontend.

## 🎯 Opgeloste Problemen

### Voor Standardisatie ❌
```javascript
// Probleem 1: Duplicaten across tables
{
  programming_languages: ["Power BI", "Python", "SQL"],
  ecosystems: ["Power BI", "Azure", "Databricks"]  // Power BI komt 2x voor!
}

// Probleem 2: Naming inconsistenties
{
  ecosystems: [
    "Power BI",
    "Microsoft Power BI",
    "PowerBI",
    "Power BI Service"  // 4 varianten voor hetzelfde tool!
  ]
}

// Probleem 3: Case inconsistenties
{
  programming_languages: ["Python", "python", "PYTHON"]  // 3x dezelfde
}
```

### Na Standardisatie ✅
```javascript
// Clean, gestandaardiseerde data
{
  programming_languages: ["Python", "SQL", "DAX"],
  ecosystems: ["Power BI", "Azure", "Databricks"]  // Geen duplicaten
}

// Consistente naming
{
  ecosystems: ["Power BI"]  // Altijd dezelfde canonical name
}
```

---

## 🗄️ Database Wijzigingen

### 1. Nieuwe Tabel: `tech_stack_aliases`

Mapped varianten naar canonical names:

```sql
CREATE TABLE tech_stack_aliases (
    id UUID PRIMARY KEY,
    alias TEXT NOT NULL UNIQUE,        -- "PowerBI", "MS Power BI"
    canonical_name TEXT NOT NULL,      -- "Power BI"
    type TEXT NOT NULL,                -- 'language' or 'ecosystem'
    notes TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);
```

**Voorbeelden:**
| Alias | Canonical Name | Type |
|-------|----------------|------|
| `PowerBI` | `Power BI` | ecosystem |
| `MS Power BI` | `Power BI` | ecosystem |
| `Microsoft Power BI` | `Power BI` | ecosystem |
| `python` | `Python` | language |
| `databricks` | `Databricks` | ecosystem |
| `K8s` | `Kubernetes` | ecosystem |

### 2. Opgeschoonde Data

**Verwijderde duplicaten:**
- 32 cross-table duplicaten (items in BEIDE tables)
- 75 naming variaties (PowerBI vs Power BI, etc.)

**Resultaat:**
- Elke tech komt slechts 1x voor
- Consistente naming (canonical names)
- Behouden: beste logo + hoogste relevance score

---

## 📊 View: `tech_stack_lookup`

De bestaande view blijft hetzelfde, maar bevat nu **clean, gestandaardiseerde data**:

```sql
CREATE VIEW tech_stack_lookup AS
  SELECT 
    name,           -- Canonical name (e.g., "Power BI")
    display_name,   -- Display name (e.g., "Microsoft Power BI")
    logo_url,       -- Logo URL (API endpoint of external)
    category,       -- Category (e.g., "BI Tool")
    'language' AS type
  FROM programming_languages 
  WHERE is_active = TRUE
  
  UNION ALL
  
  SELECT 
    name, 
    display_name, 
    logo_url, 
    category, 
    'ecosystem' AS type
  FROM ecosystems 
  WHERE is_active = TRUE;
```

### Belangrijke Velden

| Veld | Beschrijving | Voorbeeld |
|------|-------------|-----------|
| `name` | **Canonical name** (gebruik voor matching/filtering) | `"Power BI"` |
| `display_name` | **Display name** (toon in UI) | `"Microsoft Power BI"` |
| `logo_url` | Logo URL (API endpoint of external) | `"/api/tech-stack/ecosystems/{id}/logo"` |
| `category` | Categorie | `"BI Tool"`, `"Cloud Platform"` |
| `type` | Type | `"language"` of `"ecosystem"` |

---

## 🎨 Frontend Implementatie

### 1. Fetch Tech Stack Lookup (Eenmalig)

```javascript
// Fetch eenmalig bij app load, cache in memory
async function loadTechStackLookup() {
  const response = await fetch('/api/tech-stack-lookup');
  const techStack = await response.json();
  
  // Cache in state/store
  return {
    languages: techStack.filter(t => t.type === 'language'),
    ecosystems: techStack.filter(t => t.type === 'ecosystem')
  };
}

// Voorbeeld response:
[
  {
    "name": "Power BI",
    "display_name": "Microsoft Power BI",
    "logo_url": "/api/tech-stack/ecosystems/abc-123/logo",
    "category": "BI Tool",
    "type": "ecosystem"
  },
  {
    "name": "Python",
    "display_name": "Python",
    "logo_url": "/api/tech-stack/programming-languages/def-456/logo",
    "category": "General Purpose",
    "type": "language"
  }
]
```

### 2. Enrich Job Data Client-Side

```javascript
// Job data van API
const job = {
  id: "job-123",
  title: "Data Engineer",
  programming_languages: ["Python", "SQL"],  // Canonical names
  ecosystems: ["Power BI", "Azure"]          // Canonical names
};

// Enrich met logo's en display names
function enrichJobTechStack(job, techStackLookup) {
  return {
    ...job,
    programming_languages: job.programming_languages.map(name => {
      const tech = techStackLookup.languages.find(t => t.name === name);
      return tech || { name, display_name: name, logo_url: null };
    }),
    ecosystems: job.ecosystems.map(name => {
      const tech = techStackLookup.ecosystems.find(t => t.name === name);
      return tech || { name, display_name: name, logo_url: null };
    })
  };
}

// Enriched result:
{
  id: "job-123",
  title: "Data Engineer",
  programming_languages: [
    {
      name: "Python",
      display_name: "Python",
      logo_url: "/api/tech-stack/programming-languages/def-456/logo",
      category: "General Purpose"
    },
    {
      name: "SQL",
      display_name: "SQL",
      logo_url: "/api/tech-stack/programming-languages/ghi-789/logo",
      category: "Query Language"
    }
  ],
  ecosystems: [
    {
      name: "Power BI",
      display_name: "Microsoft Power BI",
      logo_url: "/api/tech-stack/ecosystems/abc-123/logo",
      category: "BI Tool"
    },
    {
      name: "Azure",
      display_name: "Microsoft Azure",
      logo_url: "/api/tech-stack/ecosystems/jkl-012/logo",
      category: "Cloud Platform"
    }
  ]
}
```

### 3. Display in Vacature Card

```jsx
// React component voorbeeld
function JobCard({ job, techStackLookup }) {
  const enrichedJob = enrichJobTechStack(job, techStackLookup);
  
  return (
    <div className="job-card">
      <h3>{job.title}</h3>
      
      {/* Programming Languages */}
      <div className="tech-stack">
        <h4>Languages</h4>
        <div className="tech-badges">
          {enrichedJob.programming_languages.map(tech => (
            <div key={tech.name} className="tech-badge">
              {tech.logo_url && (
                <img src={tech.logo_url} alt={tech.display_name} />
              )}
              <span>{tech.display_name}</span>
            </div>
          ))}
        </div>
      </div>
      
      {/* Ecosystems */}
      <div className="tech-stack">
        <h4>Tools & Platforms</h4>
        <div className="tech-badges">
          {enrichedJob.ecosystems.map(tech => (
            <div key={tech.name} className="tech-badge">
              {tech.logo_url && (
                <img src={tech.logo_url} alt={tech.display_name} />
              )}
              <span>{tech.display_name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

### 4. Filters Implementatie

```javascript
// Build filter options van tech stack lookup
function buildFilterOptions(techStackLookup) {
  return {
    languages: techStackLookup.languages
      .sort((a, b) => a.display_name.localeCompare(b.display_name))
      .map(tech => ({
        value: tech.name,        // Canonical name voor filtering
        label: tech.display_name, // Display name voor UI
        logo: tech.logo_url
      })),
    
    ecosystems: techStackLookup.ecosystems
      .sort((a, b) => a.display_name.localeCompare(b.display_name))
      .map(tech => ({
        value: tech.name,
        label: tech.display_name,
        logo: tech.logo_url
      }))
  };
}

// Filter component
function TechStackFilter({ options, selectedValues, onChange }) {
  return (
    <div className="filter-group">
      <h4>Filter by Technology</h4>
      <select 
        multiple 
        value={selectedValues} 
        onChange={e => onChange(Array.from(e.target.selectedOptions, o => o.value))}
      >
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  );
}

// Filter jobs
function filterJobs(jobs, selectedLanguages, selectedEcosystems) {
  return jobs.filter(job => {
    const hasLanguage = selectedLanguages.length === 0 || 
      selectedLanguages.some(lang => job.programming_languages.includes(lang));
    
    const hasEcosystem = selectedEcosystems.length === 0 || 
      selectedEcosystems.some(eco => job.ecosystems.includes(eco));
    
    return hasLanguage && hasEcosystem;
  });
}
```

---

## ✅ Garanties

Na deze standardisatie kun je erop vertrouwen dat:

1. **Geen duplicaten**: Elke tech komt slechts 1x voor in de lookup
2. **Consistente naming**: Altijd dezelfde canonical name (e.g., "Power BI", niet "PowerBI")
3. **Unieke logo's**: Elke tech heeft max 1 logo
4. **Case-insensitive matching**: Backend normaliseert automatisch ("powerbi" → "Power BI")
5. **Backward compatible**: Bestaande API's blijven werken

---

## 🔄 Automatische Normalisatie

De backend normaliseert automatisch nieuwe tech stack items:

```
LLM Output: "PowerBI"
    ↓
Alias Lookup: "PowerBI" → "Power BI"
    ↓
Database: Opgeslagen als "Power BI"
    ↓
Frontend: Ontvangt "Power BI"
```

**Jij hoeft niets extra's te doen!** De data is al clean wanneer je het ontvangt.

---

## 📝 Canonical Names Lijst

Hier zijn de meest voorkomende canonical names die je zult zien:

### Programming Languages
- `Python`, `SQL`, `R`, `Java`, `JavaScript`, `TypeScript`
- `C#`, `Scala`, `Go`, `Rust`, `Kotlin`, `Swift`
- `DAX`, `M`, `PL/SQL`, `T-SQL`, `PowerShell`, `Bash`

### Cloud Platforms
- `Azure`, `AWS`, `GCP`

### BI Tools
- `Power BI`, `Tableau`, `Looker`, `Qlik`

### Data Platforms
- `Databricks`, `Snowflake`, `BigQuery`, `Redshift`, `Synapse`

### Data Tools
- `dbt`, `Airflow`, `Kafka`, `Spark`, `Flink`

### Databases
- `PostgreSQL`, `MySQL`, `MongoDB`, `Redis`, `Elasticsearch`, `Oracle`

### DevOps
- `Docker`, `Kubernetes`, `Terraform`, `Git`, `Jenkins`

### ML/AI
- `TensorFlow`, `PyTorch`, `scikit-learn`, `MLflow`

---

## 🐛 Troubleshooting

### Probleem: Tech stack item heeft geen logo

**Oorzaak:** Niet alle items hebben een logo in de database.

**Oplossing:** Toon fallback icon of alleen text:
```javascript
{tech.logo_url ? (
  <img src={tech.logo_url} alt={tech.display_name} />
) : (
  <div className="tech-badge-no-logo">{tech.display_name}</div>
)}
```

### Probleem: Onbekende tech stack item

**Oorzaak:** Nieuwe tech die nog niet in de database staat.

**Oplossing:** Backend maakt automatisch nieuwe entry aan. Toon naam zonder logo:
```javascript
const tech = techStackLookup.find(t => t.name === name) || {
  name,
  display_name: name,
  logo_url: null
};
```

### Probleem: Filter toont duplicaten

**Oorzaak:** Je gebruikt `display_name` in plaats van `name` voor filtering.

**Oplossing:** Gebruik altijd `name` (canonical) voor filtering:
```javascript
// ❌ Fout
const filtered = jobs.filter(job => 
  job.ecosystems.includes(selectedDisplayName)
);

// ✅ Correct
const filtered = jobs.filter(job => 
  job.ecosystems.includes(selectedCanonicalName)
);
```

---

## 🚀 Performance Tips

### 1. Cache Tech Stack Lookup
```javascript
// Cache in Redux/Context/Zustand
const [techStackLookup, setTechStackLookup] = useState(null);

useEffect(() => {
  loadTechStackLookup().then(setTechStackLookup);
}, []); // Only once on mount
```

### 2. Memoize Enrichment
```javascript
const enrichedJobs = useMemo(() => 
  jobs.map(job => enrichJobTechStack(job, techStackLookup)),
  [jobs, techStackLookup]
);
```

### 3. Lazy Load Logos
```javascript
<img 
  src={tech.logo_url} 
  alt={tech.display_name}
  loading="lazy"  // Browser native lazy loading
/>
```

---

## 📊 API Endpoints

### GET `/api/tech-stack-lookup`
Haal alle tech stack items op (languages + ecosystems).

**Response:**
```json
[
  {
    "name": "Power BI",
    "display_name": "Microsoft Power BI",
    "logo_url": "/api/tech-stack/ecosystems/abc-123/logo",
    "category": "BI Tool",
    "type": "ecosystem"
  }
]
```

### GET `/api/tech-stack/programming-languages/{id}/logo`
Haal logo op voor een programming language.

**Response:** Binary image data (PNG/SVG)

### GET `/api/tech-stack/ecosystems/{id}/logo`
Haal logo op voor een ecosystem.

**Response:** Binary image data (PNG/SVG)

---

## 🎯 Checklist voor Frontend Developer

- [ ] Fetch `tech_stack_lookup` eenmalig bij app load
- [ ] Cache lookup data in state/store
- [ ] Enrich job data client-side met logo's en display names
- [ ] Gebruik `name` (canonical) voor filtering
- [ ] Gebruik `display_name` voor UI display
- [ ] Toon fallback voor items zonder logo
- [ ] Implement lazy loading voor logo's
- [ ] Test met verschillende tech stack combinaties

---

## 📞 Support

Bij vragen of problemen:
1. Check dit document eerst
2. Check de database migrations: `078_add_tech_stack_aliases.sql`
3. Check de code: `ingestion/tech_stack_processor.py`
4. Contacteer backend team

---

**Laatste update:** 4 december 2025  
**Versie:** 1.0  
**Status:** ✅ Production Ready
