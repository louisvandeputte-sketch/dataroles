# Frontend Implementation: Tech Stack Logos

## 🎯 Doel
Toon logo's naast programmeertalen en ecosystemen in job listings zonder performance problemen.

---

## 📊 Huidige Situatie

### Data in `vw_job_listings`:
```json
{
  "job_posting_id": "...",
  "title": "Data Engineer",
  
  // Tech stack als string arrays (BESTAAND)
  "must_have_programmeertalen": ["Python", "SQL"],
  "nice_to_have_programmeertalen": ["Java", "Scala"],
  "must_have_ecosystemen": ["Databricks", "Snowflake"],
  "nice_to_have_ecosystemen": ["Airflow", "dbt"]
}
```

### Logo data beschikbaar via:
```
GET /api/tech-stack/lookup
```

**Response (~1100 items, ~50KB):**
```json
{
  "data": [
    {
      "name": "Python",
      "display_name": "Python",
      "logo_url": "/api/programming-languages/{id}/logo",
      "category": "General Purpose",
      "type": "language"
    },
    {
      "name": "Databricks",
      "display_name": "Databricks",
      "logo_url": "/api/ecosystems/{id}/logo",
      "category": "Data Platform",
      "type": "ecosystem"
    }
    // ... ~1100 items total
  ],
  "total": 1100,
  "cache_hint": "max-age=3600"
}
```

---

## ✅ Implementatie Stappen

### **Stap 1: Create React Query Hook**

```typescript
// hooks/useTechStackLookup.ts

import { useQuery } from '@tanstack/react-query';

interface TechStackItem {
  name: string;
  display_name: string;
  logo_url: string | null;
  category: string | null;
  type: 'language' | 'ecosystem';
}

interface TechStackLookup {
  languages: Map<string, TechStackItem>;
  ecosystems: Map<string, TechStackItem>;
}

export function useTechStackLookup() {
  return useQuery<TechStackLookup>({
    queryKey: ['tech-stack-lookup'],
    queryFn: async () => {
      const response = await fetch('/api/tech-stack/lookup');
      const { data } = await response.json();
      
      // Create fast lookup maps (case-insensitive)
      const languages = new Map<string, TechStackItem>();
      const ecosystems = new Map<string, TechStackItem>();
      
      data.forEach((item: TechStackItem) => {
        const key = item.name.toLowerCase();
        if (item.type === 'language') {
          languages.set(key, item);
        } else {
          ecosystems.set(key, item);
        }
      });
      
      return { languages, ecosystems };
    },
    staleTime: 1000 * 60 * 60, // 1 hour - data changes rarely
    cacheTime: 1000 * 60 * 60 * 24, // 24 hours
    refetchOnWindowFocus: false, // Don't refetch on tab switch
  });
}
```

---

### **Stap 2: Create Enrichment Utility**

```typescript
// utils/enrichJobWithLogos.ts

import { TechStackItem, TechStackLookup } from '../hooks/useTechStackLookup';

interface JobListing {
  job_posting_id: string;
  title: string;
  must_have_programmeertalen: string[];
  nice_to_have_programmeertalen: string[];
  must_have_ecosystemen: string[];
  nice_to_have_ecosystemen: string[];
  // ... other fields
}

interface EnrichedJobListing extends JobListing {
  must_have_languages_detailed: TechStackItem[];
  nice_to_have_languages_detailed: TechStackItem[];
  must_have_ecosystems_detailed: TechStackItem[];
  nice_to_have_ecosystems_detailed: TechStackItem[];
}

/**
 * Enrich job with tech stack logos from lookup table
 * This is a fast in-memory operation (microseconds)
 */
export function enrichJobWithLogos(
  job: JobListing,
  lookup: TechStackLookup
): EnrichedJobListing {
  // Helper to get tech item with fallback
  const getTechItem = (
    name: string,
    map: Map<string, TechStackItem>,
    type: 'language' | 'ecosystem'
  ): TechStackItem => {
    const item = map.get(name.toLowerCase());
    if (item) return item;
    
    // Fallback for unmatched items (show name without logo)
    return {
      name,
      display_name: name,
      logo_url: null,
      category: null,
      type,
    };
  };

  return {
    ...job,
    must_have_languages_detailed: (job.must_have_programmeertalen || []).map(
      name => getTechItem(name, lookup.languages, 'language')
    ),
    nice_to_have_languages_detailed: (job.nice_to_have_programmeertalen || []).map(
      name => getTechItem(name, lookup.languages, 'language')
    ),
    must_have_ecosystems_detailed: (job.must_have_ecosystemen || []).map(
      name => getTechItem(name, lookup.ecosystems, 'ecosystem')
    ),
    nice_to_have_ecosystems_detailed: (job.nice_to_have_ecosystemen || []).map(
      name => getTechItem(name, lookup.ecosystems, 'ecosystem')
    ),
  };
}
```

---

### **Stap 3: Create Tech Stack Badge Component**

```typescript
// components/TechStackBadge.tsx

import React from 'react';
import { TechStackItem } from '../hooks/useTechStackLookup';

interface TechStackBadgeProps {
  tech: TechStackItem;
  variant?: 'must-have' | 'nice-to-have';
  size?: 'sm' | 'md' | 'lg';
}

export function TechStackBadge({ 
  tech, 
  variant = 'must-have',
  size = 'md' 
}: TechStackBadgeProps) {
  const sizeClasses = {
    sm: 'px-2 py-1 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base',
  };

  const variantClasses = {
    'must-have': 'bg-blue-100 text-blue-800 border-blue-300',
    'nice-to-have': 'bg-gray-100 text-gray-700 border-gray-300',
  };

  const logoSize = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  return (
    <span
      className={`
        inline-flex items-center gap-2 rounded-full border
        ${sizeClasses[size]}
        ${variantClasses[variant]}
      `}
      title={tech.category || undefined}
    >
      {tech.logo_url && (
        <img
          src={tech.logo_url}
          alt={`${tech.display_name} logo`}
          className={`${logoSize[size]} object-contain`}
          loading="lazy"
          onError={(e) => {
            // Hide image if it fails to load
            e.currentTarget.style.display = 'none';
          }}
        />
      )}
      <span className="font-medium">{tech.display_name}</span>
    </span>
  );
}
```

---

### **Stap 4: Use in Job Listing Component**

```typescript
// components/JobCard.tsx

import React from 'react';
import { useTechStackLookup } from '../hooks/useTechStackLookup';
import { enrichJobWithLogos } from '../utils/enrichJobWithLogos';
import { TechStackBadge } from './TechStackBadge';

interface JobCardProps {
  job: JobListing;
}

export function JobCard({ job }: JobCardProps) {
  // Fetch lookup table (cached after first load)
  const { data: lookup, isLoading } = useTechStackLookup();

  // Enrich job with logos (instant, in-memory)
  const enrichedJob = lookup ? enrichJobWithLogos(job, lookup) : null;

  if (isLoading || !enrichedJob) {
    return <JobCardSkeleton />;
  }

  return (
    <div className="job-card">
      <h3>{enrichedJob.title}</h3>
      
      {/* Must-have Programming Languages */}
      {enrichedJob.must_have_languages_detailed.length > 0 && (
        <div className="tech-section">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">
            Required Languages
          </h4>
          <div className="flex flex-wrap gap-2">
            {enrichedJob.must_have_languages_detailed.map((lang) => (
              <TechStackBadge
                key={lang.name}
                tech={lang}
                variant="must-have"
                size="sm"
              />
            ))}
          </div>
        </div>
      )}

      {/* Nice-to-have Programming Languages */}
      {enrichedJob.nice_to_have_languages_detailed.length > 0 && (
        <div className="tech-section">
          <h4 className="text-sm font-semibold text-gray-500 mb-2">
            Nice to Have Languages
          </h4>
          <div className="flex flex-wrap gap-2">
            {enrichedJob.nice_to_have_languages_detailed.map((lang) => (
              <TechStackBadge
                key={lang.name}
                tech={lang}
                variant="nice-to-have"
                size="sm"
              />
            ))}
          </div>
        </div>
      )}

      {/* Must-have Ecosystems */}
      {enrichedJob.must_have_ecosystems_detailed.length > 0 && (
        <div className="tech-section">
          <h4 className="text-sm font-semibold text-gray-700 mb-2">
            Required Tools & Platforms
          </h4>
          <div className="flex flex-wrap gap-2">
            {enrichedJob.must_have_ecosystems_detailed.map((eco) => (
              <TechStackBadge
                key={eco.name}
                tech={eco}
                variant="must-have"
                size="sm"
              />
            ))}
          </div>
        </div>
      )}

      {/* Nice-to-have Ecosystems */}
      {enrichedJob.nice_to_have_ecosystems_detailed.length > 0 && (
        <div className="tech-section">
          <h4 className="text-sm font-semibold text-gray-500 mb-2">
            Nice to Have Tools & Platforms
          </h4>
          <div className="flex flex-wrap gap-2">
            {enrichedJob.nice_to_have_ecosystems_detailed.map((eco) => (
              <TechStackBadge
                key={eco.name}
                tech={eco}
                variant="nice-to-have"
                size="sm"
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

---

### **Stap 5: Preload Lookup on App Start (Optional maar Aanbevolen)**

```typescript
// App.tsx or main layout component

import { useTechStackLookup } from './hooks/useTechStackLookup';

export function App() {
  // Preload lookup table on app mount
  useTechStackLookup();

  return (
    <div>
      {/* Your app content */}
    </div>
  );
}
```

---

## 📊 Performance

| Actie | Tijd | Frequentie |
|-------|------|------------|
| **Lookup fetch** | ~100ms | 1x per sessie (cached) |
| **Jobs fetch** | ~200ms | Per page load |
| **Enrich 20 jobs** | <1ms | Per render (in-memory) |
| **Total first load** | ~300ms | Eerste keer |
| **Subsequent loads** | ~200ms | Daarna (lookup cached) |

**vs. Database subqueries: ~17 seconden** ❌

---

## 🎨 Styling Tips

### **Tailwind CSS Example:**
```tsx
<TechStackBadge
  tech={tech}
  className="
    bg-gradient-to-r from-blue-50 to-blue-100
    hover:from-blue-100 hover:to-blue-200
    transition-all duration-200
    shadow-sm hover:shadow-md
  "
/>
```

### **Logo Fallback:**
Als een logo niet laadt of niet bestaat, toon dan alleen de naam:
```tsx
{tech.logo_url ? (
  <img src={tech.logo_url} alt={tech.name} />
) : (
  <div className="w-5 h-5 bg-gray-200 rounded flex items-center justify-center">
    <span className="text-xs font-bold text-gray-600">
      {tech.name.charAt(0).toUpperCase()}
    </span>
  </div>
)}
```

---

## 🔍 Debugging

### **Check if lookup is loaded:**
```typescript
const { data: lookup, isLoading, error } = useTechStackLookup();

console.log('Lookup loaded:', !!lookup);
console.log('Languages count:', lookup?.languages.size);
console.log('Ecosystems count:', lookup?.ecosystems.size);
```

### **Check if tech item is found:**
```typescript
const pythonLogo = lookup?.languages.get('python');
console.log('Python logo:', pythonLogo?.logo_url);
```

### **Test lookup endpoint:**
```bash
curl http://localhost:8000/api/tech-stack/lookup
```

---

## ⚠️ Belangrijke Notes

1. **Case-insensitive matching**: Lookup gebruikt `toLowerCase()` voor matching
2. **Fallback voor missing logos**: Component toont naam zonder logo als `logo_url` null is
3. **Caching**: React Query cached de lookup voor 1 uur
4. **Lazy loading**: Gebruik `loading="lazy"` op `<img>` tags
5. **Error handling**: Gebruik `onError` handler op images voor graceful degradation

---

## 📦 Dependencies

Zorg dat je deze packages hebt:
```json
{
  "@tanstack/react-query": "^5.x",
  "react": "^18.x"
}
```

---

## 🚀 Deployment Checklist

- [ ] Migratie 074 uitgevoerd in database ✅
- [ ] API endpoint `/api/tech-stack/lookup` werkt
- [ ] React Query hook geïmplementeerd
- [ ] Enrichment utility geïmplementeerd
- [ ] TechStackBadge component gemaakt
- [ ] JobCard component updated
- [ ] Styling toegevoegd
- [ ] Getest met verschillende jobs
- [ ] Logo fallbacks werken
- [ ] Performance getest (should be <300ms first load)

---

## 💡 Toekomstige Verbeteringen

1. **Logo CDN**: Upload logos naar CDN voor snellere loading
2. **Logo caching**: Browser cached logos automatisch (24h cache header)
3. **Virtualization**: Voor lange lijsten, gebruik virtualization (react-window)
4. **Filtering**: Filter jobs op tech stack met logo's
5. **Analytics**: Track welke tech stack het populairst is

---

## 🆘 Support

Als je problemen hebt:
1. Check browser console voor errors
2. Verify `/api/tech-stack/lookup` returns data
3. Check React Query DevTools
4. Verify logo URLs zijn correct

**Veel succes!** 🎉
