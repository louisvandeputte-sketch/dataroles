# Frontend Duplicate Tech Stack Fix

**Datum:** 4 december 2025  
**Probleem:** Duplicaten in tech stack lijst (bijv. "Azure Data Factory" 5x)  
**Oorzaak:** Frontend combineert data zonder deduplicatie  
**Oplossing:** Deduplicatie toevoegen in frontend code

---

## 🔴 Probleem

Je ziet duplicaten in de tech stack lijst:

```
Azure Data Factory (5x)
Microsoft Azure (5x)
Amazon Redshift (2x)
```

**Maar:** De database heeft **geen duplicaten**!

---

## 🔍 Root Cause

### Hoe Frontend Nu Werkt

```typescript
// useTechStackLookup.ts
const languages = new Map(); // keyed by lowercase name
const ecosystems = new Map(); // keyed by lowercase name

// Later in job enrichment:
job.programming_languages.forEach(lang => {
  const techInfo = languages.get(lang.name.toLowerCase());
  // Add to display list
});

job.ecosystems.forEach(eco => {
  const techInfo = ecosystems.get(eco.name.toLowerCase());
  // Add to display list
});
```

**Probleem:** Als een job **meerdere requirement levels** heeft voor dezelfde tech, wordt het meerdere keren toegevoegd.

### Voorbeeld

```javascript
// Job heeft:
job.ecosystems = [
  { name: "Azure Data Factory", requirement_level: "required" },
  { name: "Azure Data Factory", requirement_level: "nice_to_have" },
  { name: "Azure Data Factory", requirement_level: "required" },
  // etc.
]

// Frontend toont: "Azure Data Factory" 3x ❌
```

---

## ✅ Oplossing

### Fix 1: Deduplicatie in Job Enrichment

```typescript
// In je job enrichment functie
function enrichJobWithTechStack(job: Job, techStackLookup: TechStackLookup) {
  const techItems = new Set<string>(); // Use Set for deduplication
  
  // Add programming languages
  job.programming_languages?.forEach(lang => {
    const techInfo = techStackLookup.languages.get(lang.name.toLowerCase());
    if (techInfo) {
      techItems.add(techInfo.name); // Set automatically deduplicates
    }
  });
  
  // Add ecosystems
  job.ecosystems?.forEach(eco => {
    const techInfo = techStackLookup.ecosystems.get(eco.name.toLowerCase());
    if (techInfo) {
      techItems.add(techInfo.name);
    }
  });
  
  // Convert Set back to Array
  return {
    ...job,
    tech_stack: Array.from(techItems).map(name => {
      // Get full tech info
      return techStackLookup.languages.get(name.toLowerCase()) ||
             techStackLookup.ecosystems.get(name.toLowerCase());
    }).filter(Boolean)
  };
}
```

### Fix 2: Deduplicatie in Display Component

```typescript
// In je JobCard component
function JobCard({ job }: { job: Job }) {
  // Deduplicate tech stack before displaying
  const uniqueTechStack = useMemo(() => {
    const seen = new Set<string>();
    return job.tech_stack?.filter(tech => {
      if (seen.has(tech.name)) {
        return false; // Skip duplicate
      }
      seen.add(tech.name);
      return true;
    }) || [];
  }, [job.tech_stack]);
  
  return (
    <div>
      {uniqueTechStack.map(tech => (
        <TechBadge key={tech.name} tech={tech} />
      ))}
    </div>
  );
}
```

### Fix 3: Deduplicatie in Filters

```typescript
// In je filter component
function TechStackFilter({ jobs }: { jobs: Job[] }) {
  const allTechStack = useMemo(() => {
    const techMap = new Map<string, TechStackItem>();
    
    jobs.forEach(job => {
      job.programming_languages?.forEach(lang => {
        if (!techMap.has(lang.name)) {
          techMap.set(lang.name, lang);
        }
      });
      
      job.ecosystems?.forEach(eco => {
        if (!techMap.has(eco.name)) {
          techMap.set(eco.name, eco);
        }
      });
    });
    
    // Return unique items sorted by name
    return Array.from(techMap.values()).sort((a, b) => 
      a.name.localeCompare(b.name)
    );
  }, [jobs]);
  
  return (
    <FilterList items={allTechStack} />
  );
}
```

---

## 🎯 Aanbevolen Aanpak

### Stap 1: Update Job Enrichment (Meest Belangrijk)

Voeg deduplicatie toe in de functie die jobs enriched met tech stack data.

**Locatie:** Waarschijnlijk in `useTechStackLookup.ts` of een job enrichment hook.

**Code:**
```typescript
// Use Set to automatically deduplicate
const uniqueTechNames = new Set<string>();

job.programming_languages?.forEach(lang => {
  uniqueTechNames.add(lang.name);
});

job.ecosystems?.forEach(eco => {
  uniqueTechNames.add(eco.name);
});

// Convert to enriched tech stack items
const enrichedTechStack = Array.from(uniqueTechNames).map(name => {
  return techStackLookup.languages.get(name.toLowerCase()) ||
         techStackLookup.ecosystems.get(name.toLowerCase());
}).filter(Boolean);
```

### Stap 2: Verify in Browser

1. Open een vacature met duplicaten
2. Check console: `console.log(job.tech_stack)`
3. Verify: Geen duplicaten meer

### Stap 3: Test Filters

1. Open filters
2. Check: Geen duplicate entries
3. Select een tech → Correct aantal jobs

---

## 🐛 Debugging

### Check 1: Hoeveel Duplicaten Zijn Er?

```typescript
// In browser console
const job = jobs[0]; // Pick a job

const allTech = [
  ...(job.programming_languages || []),
  ...(job.ecosystems || [])
];

const duplicates = allTech.reduce((acc, tech) => {
  acc[tech.name] = (acc[tech.name] || 0) + 1;
  return acc;
}, {});

console.log('Duplicates:', Object.entries(duplicates).filter(([_, count]) => count > 1));
```

### Check 2: Waar Komen Duplicaten Vandaan?

```typescript
// Check if same tech has multiple requirement levels
const job = jobs[0];

job.ecosystems?.forEach(eco => {
  console.log(`${eco.name}: ${eco.requirement_level}`);
});

// If you see:
// "Azure Data Factory: required"
// "Azure Data Factory: nice_to_have"
// → That's the source of duplicates!
```

---

## 📊 Verwacht Resultaat

### Voor Fix ❌

```
Tech Stack (15 items):
- Azure Data Factory
- Azure Data Factory
- Azure Data Factory
- Azure Data Factory
- Azure Data Factory
- Python
- SQL
- ...
```

### Na Fix ✅

```
Tech Stack (8 items):
- Azure Data Factory
- Python
- SQL
- Azure Data Lake
- Databricks
- ...
```

---

## ✅ Checklist

- [ ] Deduplicatie toegevoegd in job enrichment
- [ ] Getest in browser (geen duplicaten meer)
- [ ] Filters tonen unieke items
- [ ] Job cards tonen unieke tech stack
- [ ] Performance is OK (Set operations zijn O(1))

---

## 💡 Extra: Waarom Heeft Database Geen Duplicaten?

De cleanup script heeft alle duplicate job assignments verwijderd. Maar als een job **meerdere requirement levels** heeft voor dezelfde tech, zijn dat **aparte rijen** in de database:

```sql
-- job_ecosystems table
job_posting_id | ecosystem_id | requirement_level
---------------|--------------|------------------
abc-123        | azure-df-id  | required
abc-123        | azure-df-id  | nice_to_have  ← Different requirement level!
```

Dit is **correct** in de database (verschillende requirement levels), maar moet **gededupliceerd** worden in de frontend display.

---

## 🚀 Implementatie Tijd

- **Tijd:** 15-30 minuten
- **Risico:** Laag (alleen display logic)
- **Impact:** Hoog (veel betere UX)

---

**Vragen? Check de code voorbeelden hierboven of neem contact op!**
