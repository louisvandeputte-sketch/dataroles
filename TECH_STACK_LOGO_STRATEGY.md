# Tech Stack Logo Integration Strategy

## 🎯 Probleem
De `vw_job_listings` view bevat tech stack als **string arrays**:
- `must_have_programmeertalen`: `['Python', 'SQL']`
- `nice_to_have_programmeertalen`: `['Java', 'JavaScript']`
- `must_have_ecosystemen`: `['Databricks', 'Snowflake']`
- `nice_to_have_ecosystemen`: `['AWS', 'Azure']`

Logo's zitten in aparte tabellen:
- `programming_languages` (89 entries): `name`, `display_name`, `logo_url`
- `ecosystems` (1014 entries): `name`, `display_name`, `logo_url`

**Frontend moet nu voor elke job extra queries doen om logo's op te halen → LAG!**

---

## 🔍 Analyse van Opties

### **Optie 1: JSONB Arrays met Embedded Logo's in View** ⭐ **AANBEVOLEN**

**Concept:**
```sql
-- In plaats van: ['Python', 'SQL']
-- Gebruik: 
[
  {"name": "Python", "display_name": "Python", "logo_url": "https://..."},
  {"name": "SQL", "display_name": "SQL", "logo_url": "https://..."}
]
```

**Implementatie:**
```sql
-- In vw_job_listings view:
(
  SELECT jsonb_agg(
    jsonb_build_object(
      'name', pl.name,
      'display_name', pl.display_name,
      'logo_url', pl.logo_url,
      'category', pl.category
    )
  )
  FROM unnest(e.must_have_programmeertalen) AS lang_name
  JOIN programming_languages pl ON pl.name = lang_name
) AS must_have_programmeertalen_with_logos
```

**Voordelen:**
- ✅ **Zero extra queries** - alles in één view query
- ✅ **Denormalized** - perfect voor read-heavy workloads
- ✅ **Type-safe** - JSONB met vaste structuur
- ✅ **Backwards compatible** - oude arrays blijven bestaan
- ✅ **Flexible** - kan extra metadata toevoegen (category, description)
- ✅ **PostgreSQL native** - geen applicatie logic nodig

**Nadelen:**
- ⚠️ View wordt iets complexer (maar nog steeds performant)
- ⚠️ Grotere response size (maar minimaal - logo URLs zijn klein)

**Performance:**
- View query: **+5-10ms** (subqueries zijn geïndexeerd)
- Frontend: **-100ms** (geen extra roundtrips)
- **Netto winst: ~90ms per job listing page**

---

### **Optie 2: Materialized View met Pre-joined Data**

**Concept:**
Materialized view die periodiek refresht met alle logo's embedded.

**Voordelen:**
- ✅ Snelste queries (pre-computed)
- ✅ Zero overhead tijdens read

**Nadelen:**
- ❌ **Stale data** - logo updates niet real-time
- ❌ Refresh overhead (moet scheduled worden)
- ❌ Extra storage (duplicate data)
- ❌ Complexity (refresh logic, scheduling)

**Verdict:** ❌ **Overkill** - logo's veranderen zelden, maar view moet real-time zijn voor job updates

---

### **Optie 3: Separate API Endpoint voor Logo Lookup**

**Concept:**
Frontend haalt eerst jobs op, dan aparte call voor logo's.

**Voordelen:**
- ✅ Simpele view
- ✅ Caching mogelijk op logo endpoint

**Nadelen:**
- ❌ **Extra roundtrip** - 2 API calls in plaats van 1
- ❌ **Waterfall loading** - moet wachten op eerste call
- ❌ **Complexity** - frontend moet mergen
- ❌ **N+1 problem** - als niet goed gecached

**Verdict:** ❌ **Niet optimaal** - extra latency, meer complexity

---

### **Optie 4: Client-side Logo Mapping**

**Concept:**
Frontend heeft static mapping van tech names → logo URLs.

**Voordelen:**
- ✅ Zero database overhead
- ✅ Instant rendering

**Nadelen:**
- ❌ **Duplication** - logo URLs in 2 plekken (DB + frontend)
- ❌ **Maintenance** - updates in 2 plekken
- ❌ **Inconsistency risk** - kan out-of-sync raken
- ❌ **No single source of truth**

**Verdict:** ❌ **Anti-pattern** - database is source of truth

---

## ✅ Aanbevolen Oplossing: **Optie 1 - JSONB Arrays in View**

### **Implementatie Plan**

#### **Stap 1: Extend vw_job_listings met nieuwe JSONB kolommen**

```sql
-- Migration 074: Add tech stack with logos to vw_job_listings

DROP VIEW IF EXISTS vw_job_listings;

CREATE OR REPLACE VIEW vw_job_listings AS
SELECT 
    e.job_posting_id,
    -- ... existing fields ...
    
    -- LEGACY: Keep original arrays for backwards compatibility
    e.must_have_programmeertalen,
    e.nice_to_have_programmeertalen,
    e.must_have_ecosystemen,
    e.nice_to_have_ecosystemen,
    
    -- NEW: Tech stack with logos (JSONB arrays)
    (
        SELECT COALESCE(jsonb_agg(
            jsonb_build_object(
                'name', pl.name,
                'display_name', pl.display_name,
                'logo_url', pl.logo_url,
                'category', pl.category
            ) ORDER BY pl.name
        ), '[]'::jsonb)
        FROM unnest(e.must_have_programmeertalen) AS lang_name
        LEFT JOIN programming_languages pl ON LOWER(pl.name) = LOWER(lang_name)
    ) AS must_have_languages_detailed,
    
    (
        SELECT COALESCE(jsonb_agg(
            jsonb_build_object(
                'name', pl.name,
                'display_name', pl.display_name,
                'logo_url', pl.logo_url,
                'category', pl.category
            ) ORDER BY pl.name
        ), '[]'::jsonb)
        FROM unnest(e.nice_to_have_programmeertalen) AS lang_name
        LEFT JOIN programming_languages pl ON LOWER(pl.name) = LOWER(lang_name)
    ) AS nice_to_have_languages_detailed,
    
    (
        SELECT COALESCE(jsonb_agg(
            jsonb_build_object(
                'name', ec.name,
                'display_name', ec.display_name,
                'logo_url', ec.logo_url,
                'category', ec.category
            ) ORDER BY ec.name
        ), '[]'::jsonb)
        FROM unnest(e.must_have_ecosystemen) AS eco_name
        LEFT JOIN ecosystems ec ON LOWER(ec.name) = LOWER(eco_name)
    ) AS must_have_ecosystems_detailed,
    
    (
        SELECT COALESCE(jsonb_agg(
            jsonb_build_object(
                'name', ec.name,
                'display_name', ec.display_name,
                'logo_url', ec.logo_url,
                'category', ec.category
            ) ORDER BY ec.name
        ), '[]'::jsonb)
        FROM unnest(e.nice_to_have_ecosystemen) AS eco_name
        LEFT JOIN ecosystems ec ON LOWER(ec.name) = LOWER(eco_name)
    ) AS nice_to_have_ecosystems_detailed

FROM llm_enrichment e
-- ... rest of joins ...
```

#### **Stap 2: Frontend Usage**

```typescript
// TypeScript interface
interface TechStackItem {
  name: string;
  display_name: string;
  logo_url: string | null;
  category: string | null;
}

interface JobListing {
  // ... other fields ...
  
  // NEW: Use these for display with logos
  must_have_languages_detailed: TechStackItem[];
  nice_to_have_languages_detailed: TechStackItem[];
  must_have_ecosystems_detailed: TechStackItem[];
  nice_to_have_ecosystems_detailed: TechStackItem[];
  
  // LEGACY: Still available for backwards compatibility
  must_have_programmeertalen: string[];
  nice_to_have_programmeertalen: string[];
  must_have_ecosystemen: string[];
  nice_to_have_ecosystemen: string[];
}

// React component
function TechStackBadge({ tech }: { tech: TechStackItem }) {
  return (
    <div className="tech-badge">
      {tech.logo_url && <img src={tech.logo_url} alt={tech.name} />}
      <span>{tech.display_name}</span>
    </div>
  );
}

// Usage
{job.must_have_languages_detailed.map(lang => (
  <TechStackBadge key={lang.name} tech={lang} />
))}
```

---

## 📊 Performance Impact

### **Database Side:**
- **View query time:** +5-10ms (4 subqueries with indexed joins)
- **Response size:** +2-5KB per job (minimal - just URLs)
- **Index usage:** Existing indexes on `programming_languages.name` and `ecosystems.name`

### **Frontend Side:**
- **API calls:** 1 (was: 1 + N logo lookups)
- **Render time:** Instant (no waiting for logo data)
- **Total latency reduction:** ~90-100ms per page load

### **Scalability:**
- ✅ **1000 jobs:** No problem (subqueries are fast)
- ✅ **Caching:** View results can be cached normally
- ✅ **CDN:** Logo URLs can point to CDN

---

## 🔧 Implementation Checklist

- [ ] Create migration 074 with new JSONB columns
- [ ] Test view performance with EXPLAIN ANALYZE
- [ ] Update TypeScript interfaces in frontend
- [ ] Update frontend components to use new fields
- [ ] Add fallback for missing logo_url (show text badge)
- [ ] Test with various jobs (with/without tech stack)
- [ ] Monitor query performance in production
- [ ] (Optional) Add logo_url population script for existing data

---

## 🎨 Alternative: Hybrid Approach (If Performance Issues)

If subqueries are too slow (unlikely), we can use a **hybrid**:

1. **Keep simple arrays in main view** (current state)
2. **Create separate lookup view:**
   ```sql
   CREATE VIEW tech_stack_logos AS
   SELECT name, display_name, logo_url, category, 'language' as type
   FROM programming_languages
   UNION ALL
   SELECT name, display_name, logo_url, category, 'ecosystem' as type
   FROM ecosystems;
   ```
3. **Frontend does ONE extra query** to fetch all logos (cached)
4. **Client-side merge** (fast, in-memory)

But this is **only if** Optie 1 has performance issues (which is unlikely).

---

## 🏆 Recommendation

**Implement Optie 1** - JSONB arrays with embedded logos in `vw_job_listings`.

**Why:**
- ✅ Best performance (single query, no roundtrips)
- ✅ Cleanest architecture (denormalized read view)
- ✅ Backwards compatible (keep old arrays)
- ✅ Type-safe and structured
- ✅ Easy to maintain (single source of truth)

**Next Steps:**
1. Create migration 074
2. Test performance
3. Update frontend
4. Deploy! 🚀
