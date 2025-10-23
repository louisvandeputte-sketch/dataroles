# LLM Enrichment v18 Format

## Overview
Version 18 of the LLM parser uses **English as the canonical language** with translations to Dutch (NL) and French (FR) provided in the `i18n` object.

## Expected JSON Structure

```json
{
  "data_role_type": "Data Engineer",
  "role_level": ["Technical", "Lead"],
  "seniority": ["Medior", "Senior"],
  "contract": ["Permanent", "Freelance"],
  "sourcing_type": "Direct",
  "summary_short": "As a Data Engineer you will build...",
  "summary_long": "As a Data Engineer you are part of...",
  "must_have_languages": ["Python", "SQL"],
  "nice_to_have_languages": ["Scala"],
  "must_have_ecosystems": ["Azure", "Databricks", "Airflow"],
  "nice_to_have_ecosystems": ["Kafka"],
  "must_have_spoken_languages": ["Dutch"],
  "nice_to_have_spoken_languages": ["French"],
  "i18n": {
    "nl": {
      "data_role_type": "Data Engineer",
      "role_level": ["Technisch", "Leidend"],
      "seniority": ["Medior", "Senior"],
      "contract": ["Vast", "Freelance"],
      "sourcing_type": "Rechtstreeks",
      "summary_short": "Als Data Engineer bouw je...",
      "summary_long": "Als Data Engineer maak je deel uit van..."
    },
    "fr": {
      "data_role_type": "Ingénieur Data",
      "role_level": ["Technique", "Lead"],
      "seniority": ["Intermédiaire", "Senior"],
      "contract": ["CDI", "Freelance"],
      "sourcing_type": "Direct",
      "summary_short": "En tant qu'Ingénieur Data, vous construisez...",
      "summary_long": "En tant qu'Ingénieur Data, vous faites partie de..."
    }
  }
}
```

## Translation Table

### Data Role Types
| English (Canonical) | Dutch (NL) | French (FR) |
|---------------------|------------|-------------|
| Data Engineer | Data Engineer | Ingénieur Data |
| Data Analyst | Data-analist | Analyste Data |
| Data Scientist | Data Scientist | Data Scientist |
| BI Developer | BI-ontwikkelaar | Développeur BI |
| Data Architect | Data-architect | Architecte Data |
| Data Governance | Data Governance | Gouvernance des données |
| Other | Overige datafunctie | Autre (data) |
| NIS | Niet in scope | Hors périmètre |

### Role Levels
| English (Canonical) | Dutch (NL) | French (FR) |
|---------------------|------------|-------------|
| Technical | Technisch | Technique |
| Lead | Leidend | Lead |
| Managerial | Management | Managerial |

### Seniority
| English (Canonical) | Dutch (NL) | French (FR) |
|---------------------|------------|-------------|
| Junior | Junior | Junior |
| Medior | Medior | Intermédiaire |
| Senior | Senior | Senior |

### Contract Types
| English (Canonical) | Dutch (NL) | French (FR) |
|---------------------|------------|-------------|
| Permanent | Vast | CDI |
| Freelance | Freelance | Freelance |
| Intern | Stagiair | Stage |

### Sourcing Types
| English (Canonical) | Dutch (NL) | French (FR) |
|---------------------|------------|-------------|
| Direct | Rechtstreeks | Direct |
| Agency | Wervingsbureau | Agence |

## Database Mapping

### Root Level Fields (English - Canonical)
```python
{
    "data_role_type": "Data Engineer",           # → type_datarol (legacy)
    "role_level": ["Technical", "Lead"],         # → rolniveau (legacy)
    "seniority": ["Medior", "Senior"],           # → seniority (legacy)
    "contract": ["Permanent", "Freelance"],      # → contract (legacy)
    "sourcing_type": "Direct",                   # → sourcing_type (legacy)
    "summary_short": "...",                      # → samenvatting_kort_en
    "summary_long": "...",                       # → samenvatting_lang_en
    "must_have_languages": ["Python", "SQL"],    # → must_have_programmeertalen
    "nice_to_have_languages": ["Scala"],         # → nice_to_have_programmeertalen
    "must_have_ecosystems": ["Azure"],           # → must_have_ecosystemen
    "nice_to_have_ecosystems": ["Kafka"],        # → nice_to_have_ecosystemen
    "must_have_spoken_languages": ["Dutch"],     # → must_have_talen
    "nice_to_have_spoken_languages": ["French"]  # → nice_to_have_talen
}
```

### i18n Translations
```python
{
    "i18n": {
        "nl": {
            "summary_short": "...",              # → samenvatting_kort_nl
            "summary_long": "...",               # → samenvatting_lang_nl
            "data_role_type": "Data Engineer",   # → labels JSONB
            "role_level": ["Technisch"],         # → labels JSONB
            # ... other translated labels
        },
        "fr": {
            "summary_short": "...",              # → samenvatting_kort_fr
            "summary_long": "...",               # → samenvatting_lang_fr
            "data_role_type": "Ingénieur Data",  # → labels JSONB
            "role_level": ["Technique"],         # → labels JSONB
            # ... other translated labels
        }
    }
}
```

### Database Schema
```sql
-- Summaries (3 languages)
samenvatting_kort_en TEXT  -- English (canonical)
samenvatting_kort_nl TEXT  -- Dutch translation
samenvatting_kort_fr TEXT  -- French translation
samenvatting_lang_en TEXT  -- English (canonical)
samenvatting_lang_nl TEXT  -- Dutch translation
samenvatting_lang_fr TEXT  -- French translation

-- Labels (JSONB with all translations)
labels JSONB  -- Contains en, nl, fr objects with all label translations

-- Legacy fields (backward compatibility - English values)
type_datarol TEXT
rolniveau TEXT[]
seniority TEXT[]
contract TEXT[]
sourcing_type TEXT
samenvatting_kort TEXT  -- English
samenvatting_lang TEXT  -- English
```

## Frontend Usage

### Language Tabs
The job detail page shows 3 language tabs:
- 🇬🇧 English (default)
- 🇳🇱 Nederlands
- 🇫🇷 Français

### Dynamic Content
```javascript
// Get summary in current language
getCurrentSummary('kort')  // Returns samenvatting_kort_en/nl/fr

// Get label in current language
getCurrentLabel('data_role_type')  // Returns from labels JSONB
```

### Fallback Strategy
1. Try to get value from `labels` JSONB for current language
2. If not available, fallback to legacy fields (English)
3. If still not available, show "-" or "Not available"

## Migration Notes

### Running the Migration
```bash
# Run SQL manually in Supabase SQL Editor
# File: database/migrations/005_add_multilingual_enrichment.sql
```

### Backward Compatibility
- ✅ Old enrichments (pre-v18) still work via legacy fields
- ✅ Legacy fields are still populated with English canonical values
- ✅ New enrichments use full multilingual structure
- ✅ Frontend gracefully handles both old and new formats

## Testing

### Test New Enrichment
1. Go to job detail page
2. Click "Enrich Now" or "Re-analyze"
3. Wait for enrichment to complete
4. Switch between language tabs (EN/NL/FR)
5. Verify:
   - Summaries change per language
   - Labels change per language
   - Technical fields (languages, ecosystems) stay the same

### Expected Behavior
- **English tab:** Shows canonical English values
- **Nederlands tab:** Shows Dutch translations
- **Français tab:** Shows French translations
- **Programming languages/ecosystems:** Same in all languages (language-agnostic)
- **Spoken languages:** Same in all languages (already in English)

## OpenAI Responses API Configuration

### Prompt Template
- **ID:** `pmpt_68ee0e7890788197b06ced94ab8af4d50759bbe1e2c42f88`
- **Version:** `11` (update to match your v18 prompt)

### Update Prompt Version
Update in `ingestion/llm_enrichment.py`:
```python
PROMPT_VERSION = "11"  # or "18" depending on your OpenAI setup
```
