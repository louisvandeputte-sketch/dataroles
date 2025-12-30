# Spoken Languages - Multilingual Support

**Datum:** 5 december 2025  
**Feature:** Nederlandse en Franse vertalingen voor gesproken talen  
**Impact:** Frontend kan nu "Arabisch" tonen i.p.v. "Arabic"

---

## 🎯 Probleem

De `vw_job_listings` view toonde gesproken talen alleen in het Engels:

```sql
must_have_talen: ['English', 'French', 'Arabic']
nice_to_have_talen: ['Dutch', 'German']
```

**Frontend moet dit kunnen tonen in Nederlands:**
- English → Engels
- French → Frans  
- Arabic → Arabisch
- Dutch → Nederlands
- German → Duits

---

## ✅ Oplossing

### 1. Nieuwe Master Tabel: `spoken_languages`

```sql
CREATE TABLE spoken_languages (
    id UUID PRIMARY KEY,
    name_en TEXT NOT NULL UNIQUE,  -- 'English' (canonical)
    name_nl TEXT NOT NULL,          -- 'Engels'
    name_fr TEXT NOT NULL,          -- 'Anglais'
    iso_639_1 TEXT,                 -- 'en'
    iso_639_2 TEXT,                 -- 'eng'
    is_active BOOLEAN DEFAULT TRUE
);
```

**Bevat 60+ talen:**
- Europese talen (Nederlands, Frans, Duits, Spaans, etc.)
- Aziatische talen (Chinees, Japans, Koreaans, etc.)
- Midden-Oosten talen (Arabisch, Hebreeuws, Turks, etc.)
- Afrikaanse talen (Swahili, Afrikaans, Zoeloe, etc.)
- Gebarentalen (Vlaamse Gebarentaal, etc.)

### 2. Helper Functies

**Vertaal enkele taal:**
```sql
SELECT get_language_name('English', 'nl');
-- Returns: 'Engels'

SELECT get_language_name('Arabic', 'nl');
-- Returns: 'Arabisch'

SELECT get_language_name('French', 'fr');
-- Returns: 'Français'
```

**Vertaal array van talen:**
```sql
SELECT translate_language_array(
    ARRAY['English', 'French', 'Arabic'], 
    'nl'
);
-- Returns: ['Engels', 'Frans', 'Arabisch']
```

### 3. Updated View: `vw_job_listings`

**Nieuwe kolommen toegevoegd:**

```sql
-- Original (Engels)
must_have_talen              -- ['English', 'French']
nice_to_have_talen           -- ['Dutch', 'German']

-- Nederlands (NEW)
must_have_talen_nl           -- ['Engels', 'Frans']
nice_to_have_talen_nl        -- ['Nederlands', 'Duits']

-- Frans (NEW)
must_have_talen_fr           -- ['Anglais', 'Français']
nice_to_have_talen_fr        -- ['Néerlandais', 'Allemand']
```

---

## 🚀 Implementatie

### Stap 1: Run Migrations

```bash
# Migration 079: Create spoken_languages table
cat database/migrations/079_add_spoken_languages_masterdata.sql

# Migration 080: Update vw_job_listings view
cat database/migrations/080_update_vw_job_listings_with_nl_languages.sql

# Run via Supabase Dashboard SQL Editor:
# 1. Copy inhoud van 079_add_spoken_languages_masterdata.sql
# 2. Run query
# 3. Copy inhoud van 080_update_vw_job_listings_with_nl_languages.sql
# 4. Run query
```

### Stap 2: Verify

```sql
-- Check spoken_languages table
SELECT * FROM spoken_languages WHERE name_en IN ('English', 'Dutch', 'French', 'Arabic');

-- Expected:
-- name_en  | name_nl    | name_fr
-- ---------|------------|----------
-- English  | Engels     | Anglais
-- Dutch    | Nederlands | Néerlandais
-- French   | Frans      | Français
-- Arabic   | Arabisch   | Arabe

-- Check view
SELECT 
    must_have_talen,
    must_have_talen_nl,
    must_have_talen_fr
FROM vw_job_listings
WHERE must_have_talen IS NOT NULL
LIMIT 5;
```

---

## 📊 Frontend Usage

### Voorbeeld Data

**Database output:**
```json
{
  "must_have_talen": ["English", "French"],
  "must_have_talen_nl": ["Engels", "Frans"],
  "must_have_talen_fr": ["Anglais", "Français"],
  "nice_to_have_talen": ["Dutch", "German"],
  "nice_to_have_talen_nl": ["Nederlands", "Duits"],
  "nice_to_have_talen_fr": ["Néerlandais", "Allemand"]
}
```

### Frontend Code

```typescript
// In je job listing component
interface Job {
  // ... other fields
  must_have_talen: string[];        // English names
  must_have_talen_nl: string[];     // Dutch names
  must_have_talen_fr: string[];     // French names
  nice_to_have_talen: string[];
  nice_to_have_talen_nl: string[];
  nice_to_have_talen_fr: string[];
}

// Display in Dutch
function JobCard({ job }: { job: Job }) {
  const currentLanguage = 'nl'; // or from i18n context
  
  const mustHaveLanguages = currentLanguage === 'nl' 
    ? job.must_have_talen_nl 
    : currentLanguage === 'fr'
    ? job.must_have_talen_fr
    : job.must_have_talen;
  
  return (
    <div>
      <h3>Vereiste talen:</h3>
      <ul>
        {mustHaveLanguages?.map(lang => (
          <li key={lang}>{lang}</li>
        ))}
      </ul>
    </div>
  );
}
```

### Met i18n

```typescript
import { useTranslation } from 'react-i18next';

function JobLanguages({ job }: { job: Job }) {
  const { i18n } = useTranslation();
  
  // Automatically select correct language field
  const getLanguages = (type: 'must_have' | 'nice_to_have') => {
    const lang = i18n.language; // 'nl', 'fr', or 'en'
    
    if (lang === 'nl') {
      return type === 'must_have' 
        ? job.must_have_talen_nl 
        : job.nice_to_have_talen_nl;
    } else if (lang === 'fr') {
      return type === 'must_have' 
        ? job.must_have_talen_fr 
        : job.nice_to_have_talen_fr;
    } else {
      return type === 'must_have' 
        ? job.must_have_talen 
        : job.nice_to_have_talen;
    }
  };
  
  return (
    <div>
      <h3>Vereiste talen:</h3>
      {getLanguages('must_have')?.map(lang => (
        <Badge key={lang}>{lang}</Badge>
      ))}
      
      <h3>Nice to have:</h3>
      {getLanguages('nice_to_have')?.map(lang => (
        <Badge key={lang} variant="secondary">{lang}</Badge>
      ))}
    </div>
  );
}
```

---

## 🔧 Maintenance

### Nieuwe Taal Toevoegen

```sql
INSERT INTO spoken_languages (name_en, name_nl, name_fr, iso_639_1, iso_639_2)
VALUES ('Luxembourgish', 'Luxemburgs', 'Luxembourgeois', 'lb', 'ltz');
```

### Vertaling Updaten

```sql
UPDATE spoken_languages
SET name_nl = 'Nieuw Nederlands'
WHERE name_en = 'English';
```

### Taal Deactiveren

```sql
UPDATE spoken_languages
SET is_active = FALSE
WHERE name_en = 'Old Language';
```

---

## 📋 Supported Languages (60+)

### Europese Talen
- Nederlands, Engels, Frans, Duits, Spaans, Italiaans, Portugees
- Pools, Roemeens, Grieks, Zweeds, Deens, Noors, Fins
- Russisch, Oekraïens, Tsjechisch, Slowaaks, Hongaars
- Kroatisch, Servisch, Sloveens, Bulgaars
- Albanees, Armeens, Baskisch, Catalaans
- Estisch, Lets, Litouws, Macedonisch, Maltees
- Welsh, Iers, Schots-Gaelisch

### Aziatische Talen
- Chinees, Mandarijn, Kantonees, Japans, Koreaans
- Hindi, Bengaals, Urdu, Vietnamees, Thais
- Indonesisch, Maleis, Tagalog

### Midden-Oosten
- Arabisch, Hebreeuws, Turks, Perzisch

### Afrikaanse Talen
- Swahili, Afrikaans, Zoeloe

### Gebarentalen
- Gebarentaal, Vlaamse Gebarentaal, Amerikaanse Gebarentaal

---

## ✅ Voordelen

1. **Betere UX** - Gebruikers zien talen in hun eigen taal
2. **Consistent** - Zelfde aanpak als andere multilingual velden (city_name_nl, sector_nl, etc.)
3. **Schaalbaar** - Makkelijk nieuwe talen toevoegen
4. **ISO codes** - Standaard ISO 639-1 en ISO 639-2 codes
5. **Backward compatible** - Originele `must_have_talen` blijft bestaan

---

## 🐛 Troubleshooting

### Probleem: Taal niet gevonden

**Symptoom:**
```sql
SELECT must_have_talen_nl FROM vw_job_listings;
-- Returns: ['Engels', 'Unknown Language']
```

**Oplossing:**
```sql
-- Check welke talen niet in master table zitten
SELECT DISTINCT unnest(must_have_talen) as language
FROM llm_enrichment
WHERE must_have_talen IS NOT NULL
EXCEPT
SELECT name_en FROM spoken_languages;

-- Voeg ontbrekende talen toe
INSERT INTO spoken_languages (name_en, name_nl, name_fr)
VALUES ('Unknown Language', 'Onbekende Taal', 'Langue Inconnue');
```

### Probleem: View toont NULL

**Symptoom:**
```sql
SELECT must_have_talen_nl FROM vw_job_listings;
-- Returns: NULL (but must_have_talen has data)
```

**Oplossing:**
```sql
-- Check of functies bestaan
SELECT proname FROM pg_proc WHERE proname = 'translate_language_array';

-- Re-run migration 079 als functies ontbreken
```

---

## 📊 Impact

**Voor:**
```
Vereiste talen: English, French, Arabic
```

**Na:**
```
Vereiste talen: Engels, Frans, Arabisch
```

**Veel betere UX voor Nederlandse gebruikers!** 🎉

---

**Implementatie tijd:** 15 minuten  
**Risico:** Laag (alleen view update)  
**Backward compatible:** Ja (originele velden blijven bestaan)
