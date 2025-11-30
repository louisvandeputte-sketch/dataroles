# Tech Stack Lookup API - Database Info

## ✅ Database View Naam

**View naam:** `tech_stack_lookup` (GEEN `vw_` prefix!)

---

## 📊 View Structuur

```sql
CREATE OR REPLACE VIEW tech_stack_lookup AS
SELECT 
    name,              -- string (e.g., "Python", "Databricks")
    display_name,      -- string (e.g., "Python", "Databricks")
    logo_url,          -- string | null (e.g., "/api/programming-languages/{id}/logo")
    category,          -- string | null (e.g., "General Purpose", "Data Platform")
    'language' AS type -- 'language' | 'ecosystem'
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

---

## 📋 Exacte TypeScript Interface

```typescript
interface TechStackItem {
  name: string;              // "Python", "Databricks", etc.
  display_name: string;      // "Python", "Databricks", etc.
  logo_url: string | null;   // "/api/programming-languages/{id}/logo" or null
  category: string | null;   // "General Purpose", "Data Platform", etc. or null
  type: 'language' | 'ecosystem';  // Literal type
}
```

---

## 🔍 Database Tabellen

### **1. `programming_languages` tabel**
```sql
CREATE TABLE programming_languages (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,           -- ✅ Used in view
    display_name TEXT NOT NULL,          -- ✅ Used in view
    logo_url TEXT,                       -- ✅ Used in view
    category TEXT,                       -- ✅ Used in view
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,      -- ✅ Filtered in view
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Aantal records:** ~89 programming languages

### **2. `ecosystems` tabel**
```sql
CREATE TABLE ecosystems (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,           -- ✅ Used in view
    display_name TEXT NOT NULL,          -- ✅ Used in view
    logo_url TEXT,                       -- ✅ Used in view
    category TEXT,                       -- ✅ Used in view
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,      -- ✅ Filtered in view
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Aantal records:** ~1014 ecosystems

---

## 🎯 Edge Function Query

### **Optie 1: Query de View (AANBEVOLEN)**

```typescript
// Edge function code
const { data, error } = await supabase
  .from('tech_stack_lookup')  // ✅ View naam (GEEN vw_ prefix!)
  .select('*');

if (error) throw error;

return new Response(
  JSON.stringify({ 
    data, 
    total: data.length,
    cache_hint: 'max-age=3600' 
  }),
  { 
    headers: { 
      'Content-Type': 'application/json',
      'Cache-Control': 'public, max-age=3600'
    } 
  }
);
```

### **Optie 2: Query Beide Tabellen (als view niet werkt)**

```typescript
// Fallback: query both tables separately
const [languagesResult, ecosystemsResult] = await Promise.all([
  supabase
    .from('programming_languages')
    .select('name, display_name, logo_url, category')
    .eq('is_active', true),
  supabase
    .from('ecosystems')
    .select('name, display_name, logo_url, category')
    .eq('is_active', true)
]);

if (languagesResult.error) throw languagesResult.error;
if (ecosystemsResult.error) throw ecosystemsResult.error;

// Combine and add type field
const data = [
  ...languagesResult.data.map(item => ({ ...item, type: 'language' as const })),
  ...ecosystemsResult.data.map(item => ({ ...item, type: 'ecosystem' as const }))
];

return new Response(
  JSON.stringify({ 
    data, 
    total: data.length,
    cache_hint: 'max-age=3600' 
  }),
  { 
    headers: { 
      'Content-Type': 'application/json',
      'Cache-Control': 'public, max-age=3600'
    } 
  }
);
```

---

## 🔐 Supabase Permissions

Zorg dat de edge function toegang heeft tot:

```sql
-- Grant SELECT on view
GRANT SELECT ON tech_stack_lookup TO anon, authenticated;

-- Grant SELECT on tables (if using Optie 2)
GRANT SELECT ON programming_languages TO anon, authenticated;
GRANT SELECT ON ecosystems TO anon, authenticated;
```

---

## 📊 Expected Response Format

```json
{
  "data": [
    {
      "name": "Python",
      "display_name": "Python",
      "logo_url": "/api/programming-languages/123e4567-e89b-12d3-a456-426614174000/logo",
      "category": "General Purpose",
      "type": "language"
    },
    {
      "name": "Databricks",
      "display_name": "Databricks",
      "logo_url": "/api/ecosystems/987fcdeb-51a2-43f7-8b9c-123456789abc/logo",
      "category": "Data Platform",
      "type": "ecosystem"
    },
    {
      "name": "SQL",
      "display_name": "SQL",
      "logo_url": null,
      "category": "Query Language",
      "type": "language"
    }
    // ... ~1100 items total
  ],
  "total": 1100,
  "cache_hint": "max-age=3600"
}
```

---

## ✅ Verification Checklist

- [ ] View `tech_stack_lookup` bestaat in database
- [ ] View heeft kolommen: `name`, `display_name`, `logo_url`, `category`, `type`
- [ ] Edge function heeft SELECT permissies op view
- [ ] Response bevat ~1100 items
- [ ] Response size is ~50KB
- [ ] Cache headers zijn correct ingesteld

---

## 🧪 Test Query

Test in Supabase SQL Editor:

```sql
-- Check if view exists
SELECT * FROM tech_stack_lookup LIMIT 10;

-- Count total items
SELECT 
  type,
  COUNT(*) as count
FROM tech_stack_lookup
GROUP BY type;

-- Expected output:
-- type       | count
-- -----------+-------
-- language   | ~89
-- ecosystem  | ~1014
```

---

## 🆘 Troubleshooting

### **Error: "relation tech_stack_lookup does not exist"**
➡️ Run migration 074: `/database/migrations/074_create_tech_stack_lookup_view.sql`

### **Error: "permission denied for view tech_stack_lookup"**
➡️ Run: `GRANT SELECT ON tech_stack_lookup TO anon, authenticated;`

### **Empty response**
➡️ Check: `SELECT COUNT(*) FROM programming_languages WHERE is_active = TRUE;`
➡️ Check: `SELECT COUNT(*) FROM ecosystems WHERE is_active = TRUE;`

### **logo_url is always null**
➡️ Logo's worden apart geüpload via API endpoints
➡️ Check: `SELECT COUNT(*) FROM programming_languages WHERE logo_url IS NOT NULL;`

---

## 📞 Contact

Als er problemen zijn met de database setup, laat het me weten!
