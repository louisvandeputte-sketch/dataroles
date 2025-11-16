# Company Fields in llm_enrichment_active View

## Overzicht

De `llm_enrichment_active` view bevat nu uitgebreide company informatie in alle talen (NL/EN/FR).

## Nieuwe Company Velden (Migration 043)

### Company Basis Info
```sql
company_name          -- Bedrijfsnaam
logo_url             -- Company logo URL
```

### Company Sector (Multilingual)
```sql
sector_en            -- Sector in Engels (bijv. "Technology", "Finance")
company_sector_nl    -- Bedrijfsomschrijving in Nederlands (bevat sector info)
company_sector_en    -- Company description in English (contains sector info)
company_sector_fr    -- Description de l'entreprise en français (contient info secteur)
```

### Company Size Category (Multilingual)
```sql
size_category        -- Enum: startup, scaleup, sme, established_enterprise, 
                     --       corporate, public_company, government, unknown
size_summary_nl      -- Nederlandse samenvatting van bedrijfsgrootte
size_summary_en      -- English summary of company size
size_summary_fr      -- Résumé français de la taille de l'entreprise
size_confidence      -- Confidence score (0-1) voor classificatie
```

### Additional Company Metadata
```sql
aantal_werknemers    -- Geschat aantal werknemers
founded_year         -- Oprichtingsjaar
industry             -- Industrie (originele data)
```

## API Response Structuur

### Via /api/jobs/ Endpoint

```json
{
  "jobs": [{
    "id": "123",
    "title": "Senior Data Engineer",
    "llm_enrichment": {
      "type_datarol": "Data Engineer",
      
      "company_name": "TechCorp Belgium",
      "logo_url": "https://...",
      
      "sector_en": "Technology",
      "company_sector_nl": "Technologiebedrijf gespecialiseerd in AI en data analytics...",
      "company_sector_en": "Technology company specialized in AI and data analytics...",
      "company_sector_fr": "Entreprise technologique spécialisée en IA et analytique de données...",
      
      "size_category": "scaleup",
      "size_summary_nl": "Scaleup met 50-200 werknemers in groeifase",
      "size_summary_en": "Scaleup with 50-200 employees in growth phase",
      "size_summary_fr": "Scaleup avec 50-200 employés en phase de croissance",
      "size_confidence": 0.85,
      
      "aantal_werknemers": "100-150",
      "founded_year": 2018,
      "industry": "Information Technology"
    }
  }]
}
```

## Frontend Gebruik

### Filter op Company Size Category

```javascript
// Filter op startups
fetch('/api/jobs/?type_datarol=Data Engineer')
  .then(res => res.json())
  .then(data => {
    const startupJobs = data.jobs.filter(job => 
      job.llm_enrichment?.size_category === 'startup'
    );
  });
```

### Display Company Info in Gewenste Taal

```javascript
function displayCompanyInfo(job, language = 'nl') {
  const enrichment = job.llm_enrichment;
  
  // Sector beschrijving
  const sectorKey = `company_sector_${language}`;
  const sector = enrichment[sectorKey] || enrichment.sector_en;
  
  // Size summary
  const sizeKey = `size_summary_${language}`;
  const sizeInfo = enrichment[sizeKey] || enrichment.size_summary_en;
  
  return {
    name: enrichment.company_name,
    logo: enrichment.logo_url,
    sector: sector,
    size: sizeInfo,
    sizeCategory: enrichment.size_category,
    employees: enrichment.aantal_werknemers,
    founded: enrichment.founded_year
  };
}

// Gebruik
const companyInfo = displayCompanyInfo(job, 'nl');
console.log(companyInfo);
// {
//   name: "TechCorp Belgium",
//   sector: "Technologiebedrijf gespecialiseerd in...",
//   size: "Scaleup met 50-200 werknemers...",
//   sizeCategory: "scaleup",
//   employees: "100-150",
//   founded: 2018
// }
```

### UI Component Voorbeeld (Alpine.js)

```html
<div x-data="{ language: 'nl' }">
  <!-- Language Selector -->
  <select x-model="language">
    <option value="nl">Nederlands</option>
    <option value="en">English</option>
    <option value="fr">Français</option>
  </select>
  
  <!-- Company Info Card -->
  <template x-for="job in jobs" :key="job.id">
    <div class="company-card">
      <img :src="job.llm_enrichment?.logo_url" alt="Company logo">
      <h3 x-text="job.llm_enrichment?.company_name"></h3>
      
      <!-- Sector (multilingual) -->
      <p class="sector" 
         x-text="job.llm_enrichment?.[`company_sector_${language}`] || job.llm_enrichment?.sector_en">
      </p>
      
      <!-- Size Category Badge -->
      <span class="badge" 
            :class="`badge-${job.llm_enrichment?.size_category}`"
            x-text="job.llm_enrichment?.size_category">
      </span>
      
      <!-- Size Summary (multilingual) -->
      <p class="size-info"
         x-text="job.llm_enrichment?.[`size_summary_${language}`]">
      </p>
      
      <!-- Metadata -->
      <div class="metadata">
        <span x-show="job.llm_enrichment?.aantal_werknemers">
          👥 <span x-text="job.llm_enrichment.aantal_werknemers"></span> werknemers
        </span>
        <span x-show="job.llm_enrichment?.founded_year">
          📅 Opgericht in <span x-text="job.llm_enrichment.founded_year"></span>
        </span>
      </div>
    </div>
  </template>
</div>
```

## Size Category Waarden

```javascript
const sizeCategories = {
  'startup': {
    nl: 'Startup',
    en: 'Startup',
    fr: 'Startup',
    color: 'green'
  },
  'scaleup': {
    nl: 'Scaleup',
    en: 'Scaleup',
    fr: 'Scaleup',
    color: 'blue'
  },
  'sme': {
    nl: 'KMO',
    en: 'SME',
    fr: 'PME',
    color: 'yellow'
  },
  'established_enterprise': {
    nl: 'Gevestigde Onderneming',
    en: 'Established Enterprise',
    fr: 'Entreprise Établie',
    color: 'orange'
  },
  'corporate': {
    nl: 'Corporate',
    en: 'Corporate',
    fr: 'Corporate',
    color: 'purple'
  },
  'public_company': {
    nl: 'Beursgenoteerd',
    en: 'Public Company',
    fr: 'Société Cotée',
    color: 'indigo'
  },
  'government': {
    nl: 'Overheid',
    en: 'Government',
    fr: 'Gouvernement',
    color: 'gray'
  },
  'unknown': {
    nl: 'Onbekend',
    en: 'Unknown',
    fr: 'Inconnu',
    color: 'gray'
  }
};
```

## Database Query Voorbeelden

### Direct Query op View

```sql
-- Get jobs with company info in Dutch
SELECT 
  job_posting_id,
  title,
  company_name,
  company_sector_nl,
  size_category,
  size_summary_nl,
  aantal_werknemers
FROM llm_enrichment_active
WHERE type_datarol = 'Data Engineer'
  AND size_category = 'startup'
LIMIT 10;
```

### Filter op Sector (Engels)

```sql
SELECT 
  company_name,
  sector_en,
  COUNT(*) as job_count
FROM llm_enrichment_active
WHERE sector_en ILIKE '%technology%'
GROUP BY company_name, sector_en
ORDER BY job_count DESC;
```

### Companies by Size Category

```sql
SELECT 
  size_category,
  COUNT(DISTINCT company_name) as company_count,
  COUNT(*) as job_count
FROM llm_enrichment_active
WHERE size_category IS NOT NULL
GROUP BY size_category
ORDER BY job_count DESC;
```

## Performance Notes

### Indexes
- ✅ `idx_company_master_data_sector` op `sector_en`
- ✅ `idx_company_size_category` op `size_category`
- ✅ View gebruikt LEFT JOINs voor optimale performance

### Best Practices
1. **Gebruik de view** in plaats van directe table joins
2. **Filter eerst op type_datarol** voor snelste queries
3. **Cache company info** in frontend voor hergebruik
4. **Fallback naar Engels** als vertaling ontbreekt

## Migration Info

- **File**: `database/migrations/043_add_company_fields_to_enrichment_view.sql`
- **Date**: 2025-11-16
- **Changes**: 
  - Added company_name, logo_url
  - Added sector in NL/EN/FR (via bedrijfsomschrijving fields)
  - Added size_category and size_summary in NL/EN/FR
  - Added aantal_werknemers, founded_year, industry
  - Updated view comment with new fields

## Samenvatting

✅ **Company Sector**: Beschikbaar in NL/EN/FR via `company_sector_{nl|en|fr}`  
✅ **Company Category**: `size_category` enum + summaries in NL/EN/FR  
✅ **Multilingual**: Alle company info in 3 talen  
✅ **Performance**: Geoptimaliseerd met indexes  
✅ **API Ready**: Direct beschikbaar via `/api/jobs/` endpoint
