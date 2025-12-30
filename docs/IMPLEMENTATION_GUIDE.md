# Tech Stack Standardization - Implementation Guide

**Datum:** 4 december 2025  
**Implementatie tijd:** ~2-3 uur  
**Risico:** Laag (backward compatible)

---

## 📋 Overzicht

Deze guide beschrijft de stappen om de tech stack standardisatie te implementeren in productie.

### Wat wordt geïmplementeerd?

1. ✅ **Alias mapping table** - Normaliseert varianten naar canonical names
2. ✅ **Data cleanup** - Verwijdert duplicaten en inconsistenties
3. ✅ **Automatische normalisatie** - Backend normaliseert nieuwe data automatisch
4. ✅ **Frontend documentatie** - Guide voor frontend developer

### Resultaat

- **32 cross-table duplicaten** opgelost
- **75 naming variaties** gestandaardiseerd
- **Clean, consistente data** voor frontend
- **Automatische normalisatie** voor nieuwe jobs

---

## 🚀 Implementatie Stappen

### Stap 1: Run Database Migration (5 min)

De migration maakt de `tech_stack_aliases` tabel aan en vult deze met 100+ common aliases.

```bash
# Navigeer naar project directory
cd /Users/louisvandeputte/datarole

# Check migration file
cat database/migrations/078_add_tech_stack_aliases.sql

# Run migration via Supabase CLI of SQL editor
# Optie A: Supabase CLI
supabase db push

# Optie B: Supabase Dashboard
# 1. Open Supabase Dashboard
# 2. Ga naar SQL Editor
# 3. Kopieer inhoud van 078_add_tech_stack_aliases.sql
# 4. Run query
```

**Verificatie:**
```sql
-- Check of tabel bestaat
SELECT COUNT(*) FROM tech_stack_aliases;
-- Verwacht: ~100+ rows

-- Check voorbeelden
SELECT * FROM tech_stack_aliases WHERE canonical_name = 'Power BI';
-- Verwacht: PowerBI, MS Power BI, Microsoft Power BI, etc.
```

---

### Stap 2: Analyze Current Duplicates (10 min)

Run het analyse script om te zien wat er opgeschoond gaat worden.

```bash
# Run analyse (safe, read-only)
PYTHONPATH=/Users/louisvandeputte/datarole python3 scripts/analyze_tech_stack_duplicates.py

# Output wordt getoond in terminal + saved to tech_stack_analysis.json
```

**Review de output:**
- Hoeveel duplicaten zijn er?
- Welke items worden gemerged?
- Zijn de canonical choices logisch?

**Voorbeeld output:**
```
📊 STATISTICS
Total Programming Languages: 89
Total Ecosystems: 1000
Cross-Table Duplicates: 32
Naming Variation Groups: 75
Recommended Merges: 75

🔴 CROSS-TABLE DUPLICATES
  • Power BI (in both tables)
  • Python (in both tables)
  • SQL (in both tables)
  ...

✅ RECOMMENDED MERGES
  1. Keep: Power BI (ecosystem)
     Merge: Power BI (language), PowerBI (ecosystem)
  ...
```

---

### Stap 3: Dry-Run Cleanup (15 min)

Run de cleanup script in **dry-run mode** (geen changes).

```bash
# Dry-run (safe, no database changes)
PYTHONPATH=/Users/louisvandeputte/datarole python3 scripts/cleanup_tech_stack_duplicates.py

# Output wordt getoond + saved to cleanup_report.json
```

**Review de dry-run output:**
- Welke entries worden gedeactiveerd?
- Hoeveel job assignments worden ge-update?
- Zijn er onverwachte merges?

**Voorbeeld output:**
```
CLEANUP SUMMARY
Mode: DRY RUN (no changes made)

Deactivated entries: 107
Job assignments updated: 1,234
Aliases created: 107

--- Deactivated Entries ---
  • PowerBI (ecosystem) - 45 jobs
    Reason: Naming variation: PowerBI → Power BI
  • python (language) - 12 jobs
    Reason: Naming variation: python → Python
  ...

⚠️  This was a DRY RUN. No changes were made.
Run with --execute flag to apply changes.
```

**⚠️ BELANGRIJK:** Review de output zorgvuldig voordat je verder gaat!

---

### Stap 4: Backup Database (5 min)

Maak een backup voordat je de cleanup uitvoert.

```bash
# Optie A: Supabase Dashboard
# 1. Open Supabase Dashboard
# 2. Ga naar Database → Backups
# 3. Klik "Create backup"

# Optie B: pg_dump (als je direct database access hebt)
pg_dump $DATABASE_URL > backup_before_cleanup_$(date +%Y%m%d_%H%M%S).sql
```

---

### Stap 5: Execute Cleanup (30 min)

⚠️ **LET OP:** Dit maakt database changes!

```bash
# Execute cleanup (maakt database changes!)
PYTHONPATH=/Users/louisvandeputte/datarole python3 scripts/cleanup_tech_stack_duplicates.py --execute

# Monitor de output voor errors
```

**Wat gebeurt er?**
1. Duplicaten worden gedeactiveerd (`is_active = false`)
2. Job assignments worden ge-update naar canonical entries
3. Aliases worden aangemaakt voor gemerged items

**Verificatie na cleanup:**
```sql
-- Check aantal active items
SELECT 
  (SELECT COUNT(*) FROM programming_languages WHERE is_active = true) as active_languages,
  (SELECT COUNT(*) FROM ecosystems WHERE is_active = true) as active_ecosystems;
-- Verwacht: ~89 languages, ~900 ecosystems (was 1000)

-- Check cross-table duplicates (should be 0)
SELECT name, COUNT(*) 
FROM (
  SELECT name FROM programming_languages WHERE is_active = true
  UNION ALL
  SELECT name FROM ecosystems WHERE is_active = true
) t
GROUP BY name
HAVING COUNT(*) > 1;
-- Verwacht: 0 rows

-- Check aliases created
SELECT COUNT(*) FROM tech_stack_aliases;
-- Verwacht: ~200+ rows (100 from migration + 100 from cleanup)
```

---

### Stap 6: Test Backend Normalization (10 min)

Test of de automatische normalisatie werkt.

```python
# Test script
from ingestion.tech_stack_processor import normalize_tech_name

# Test cases
test_cases = [
    ("PowerBI", "ecosystem", "Power BI"),
    ("python", "language", "Python"),
    ("MS Power BI", "ecosystem", "Power BI"),
    ("K8s", "ecosystem", "Kubernetes"),
    ("databricks", "ecosystem", "Databricks"),
]

for input_name, tech_type, expected in test_cases:
    result = normalize_tech_name(input_name, tech_type)
    status = "✅" if result == expected else "❌"
    print(f"{status} {input_name} ({tech_type}) → {result} (expected: {expected})")
```

**Run test:**
```bash
PYTHONPATH=/Users/louisvandeputte/datarole python3 -c "
from ingestion.tech_stack_processor import normalize_tech_name

tests = [
    ('PowerBI', 'ecosystem', 'Power BI'),
    ('python', 'language', 'Python'),
    ('MS Power BI', 'ecosystem', 'Power BI'),
]

for inp, typ, exp in tests:
    result = normalize_tech_name(inp, typ)
    print(f'✅ {inp} → {result}' if result == exp else f'❌ {inp} → {result} (expected {exp})')
"
```

---

### Stap 7: Deploy Code Changes (15 min)

Deploy de code changes naar productie.

```bash
# Check welke files zijn aangepast
git status

# Files die gecommit moeten worden:
# - database/migrations/078_add_tech_stack_aliases.sql
# - database/client.py (nieuwe methods)
# - ingestion/tech_stack_processor.py (normalization)
# - scripts/analyze_tech_stack_duplicates.py
# - scripts/cleanup_tech_stack_duplicates.py
# - docs/FRONTEND_TECH_STACK_STANDARDIZATION.md
# - docs/IMPLEMENTATION_GUIDE.md

# Commit changes
git add database/migrations/078_add_tech_stack_aliases.sql
git add database/client.py
git add ingestion/tech_stack_processor.py
git add scripts/analyze_tech_stack_duplicates.py
git add scripts/cleanup_tech_stack_duplicates.py
git add docs/

git commit -m "feat: Add tech stack standardization with alias mapping

- Add tech_stack_aliases table for name normalization
- Cleanup 32 cross-table duplicates and 75 naming variations
- Auto-normalize tech stack names in ingestion pipeline
- Add frontend documentation for standardized data

Resolves: Power BI variants, case inconsistencies, cross-table duplicates"

# Push to repository
git push origin main

# Deploy to production (afhankelijk van je deployment process)
# Bijvoorbeeld: Vercel, Netlify, manual deployment, etc.
```

---

### Stap 8: Verify in Production (10 min)

Test of alles werkt in productie.

**Backend verificatie:**
```bash
# Test API endpoint (als je een tech stack endpoint hebt)
curl https://your-api.com/api/tech-stack-lookup | jq '.[] | select(.name == "Power BI")'

# Verwacht: 1 result (geen duplicaten)
```

**Database verificatie:**
```sql
-- Check tech_stack_lookup view
SELECT * FROM tech_stack_lookup WHERE name ILIKE '%power%bi%';
-- Verwacht: 1 row met name = "Power BI"

-- Check geen duplicaten
SELECT name, COUNT(*) as count
FROM tech_stack_lookup
GROUP BY name
HAVING COUNT(*) > 1;
-- Verwacht: 0 rows
```

**Frontend verificatie:**
- Open dashboard
- Check of filters geen duplicaten tonen
- Check of vacature cards clean tech stack tonen
- Check of logo's correct laden

---

### Stap 9: Share Documentation met Frontend Developer (5 min)

Stuur de frontend documentatie naar je frontend developer.

```bash
# Locatie van documentatie
cat docs/FRONTEND_TECH_STACK_STANDARDIZATION.md

# Of deel via:
# - Email
# - Slack/Teams
# - Confluence/Notion
# - GitHub README link
```

**Belangrijkste punten voor frontend:**
- ✅ Data is nu clean en gestandaardiseerd
- ✅ Geen duplicaten meer
- ✅ Gebruik `name` voor filtering, `display_name` voor UI
- ✅ Fetch `tech_stack_lookup` eenmalig en cache
- ✅ Enrich job data client-side

---

## 🎯 Post-Implementation

### Monitoring (Eerste Week)

Monitor de volgende metrics:

1. **Nieuwe tech stack items**
   ```sql
   -- Check nieuwe items per dag
   SELECT 
     DATE(created_at) as date,
     COUNT(*) as new_items
   FROM (
     SELECT created_at FROM programming_languages WHERE created_at > NOW() - INTERVAL '7 days'
     UNION ALL
     SELECT created_at FROM ecosystems WHERE created_at > NOW() - INTERVAL '7 days'
   ) t
   GROUP BY DATE(created_at)
   ORDER BY date DESC;
   ```

2. **Normalization rate**
   ```sql
   -- Check hoeveel aliases worden gebruikt
   SELECT 
     canonical_name,
     COUNT(*) as alias_count
   FROM tech_stack_aliases
   GROUP BY canonical_name
   ORDER BY alias_count DESC
   LIMIT 20;
   ```

3. **Duplicaten detectie**
   ```sql
   -- Check of er nieuwe duplicaten ontstaan
   SELECT name, COUNT(*) 
   FROM tech_stack_lookup
   GROUP BY name
   HAVING COUNT(*) > 1;
   -- Should be 0
   ```

### Maintenance (Maandelijks)

1. **Review nieuwe tech stack items**
   - Check of er nieuwe varianten zijn die aliases nodig hebben
   - Voeg aliases toe indien nodig

2. **Update aliases**
   ```sql
   -- Voeg nieuwe alias toe
   INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes)
   VALUES ('New Variant', 'Canonical Name', 'ecosystem', 'Added via maintenance');
   ```

3. **Check data quality**
   - Run analyse script maandelijks
   - Check of er nieuwe duplicaten zijn ontstaan

---

## 🐛 Troubleshooting

### Probleem: Migration faalt

**Error:** `relation "tech_stack_aliases" already exists`

**Oplossing:**
```sql
-- Check of tabel al bestaat
SELECT * FROM tech_stack_aliases LIMIT 1;

-- Als tabel bestaat maar leeg is, run alleen de INSERT statements
-- Kopieer alleen de INSERT INTO statements uit de migration
```

---

### Probleem: Cleanup script faalt

**Error:** `Failed to update assignment`

**Oplossing:**
1. Check de error message in detail
2. Mogelijk is er een foreign key constraint issue
3. Run dry-run opnieuw om te zien welke assignment faalt
4. Manually fix die specifieke assignment

```sql
-- Check problematic assignment
SELECT * FROM job_programming_languages WHERE id = 'problematic-id';

-- Manually update if needed
UPDATE job_programming_languages 
SET programming_language_id = 'canonical-id'
WHERE id = 'problematic-id';
```

---

### Probleem: Frontend toont nog duplicaten

**Oorzaak:** Frontend cache is niet ge-refresh

**Oplossing:**
1. Hard refresh browser (Cmd+Shift+R / Ctrl+Shift+R)
2. Clear localStorage/sessionStorage
3. Check of API correct data returned:
   ```bash
   curl https://your-api.com/api/tech-stack-lookup | jq 'group_by(.name) | map(select(length > 1))'
   # Should be empty array []
   ```

---

### Probleem: Nieuwe tech wordt niet genormaliseerd

**Oorzaak:** Alias bestaat niet in database

**Oplossing:**
```sql
-- Voeg alias toe
INSERT INTO tech_stack_aliases (alias, canonical_name, type, notes)
VALUES ('New Variant', 'Canonical Name', 'ecosystem', 'Added manually');

-- Re-process affected jobs (optional)
-- Dit is alleen nodig als je oude jobs wilt updaten
```

---

## 📊 Success Criteria

De implementatie is succesvol als:

- ✅ Migration is succesvol uitgevoerd
- ✅ Cleanup script heeft geen errors
- ✅ Geen cross-table duplicaten meer (`SELECT name, COUNT(*) ... HAVING COUNT(*) > 1` = 0 rows)
- ✅ Naming variaties zijn opgelost (Power BI, PowerBI, etc. → allemaal "Power BI")
- ✅ Backend normaliseert automatisch nieuwe data
- ✅ Frontend toont clean, consistente data
- ✅ Filters tonen geen duplicaten
- ✅ Logo's laden correct

---

## 📞 Support

Bij problemen tijdens implementatie:

1. **Check logs**
   - Backend logs voor normalization errors
   - Database logs voor constraint violations

2. **Run diagnostics**
   ```bash
   # Re-run analyse
   PYTHONPATH=/Users/louisvandeputte/datarole python3 scripts/analyze_tech_stack_duplicates.py
   
   # Check database state
   psql $DATABASE_URL -f diagnostics.sql
   ```

3. **Rollback indien nodig**
   ```sql
   -- Restore from backup
   psql $DATABASE_URL < backup_before_cleanup_YYYYMMDD_HHMMSS.sql
   
   -- Of manual rollback:
   -- 1. Reactivate deactivated entries
   UPDATE programming_languages SET is_active = true WHERE is_active = false;
   UPDATE ecosystems SET is_active = true WHERE is_active = false;
   
   -- 2. Drop aliases table
   DROP TABLE tech_stack_aliases;
   ```

---

## 🎉 Completion Checklist

- [ ] Stap 1: Database migration uitgevoerd
- [ ] Stap 2: Duplicaten analyse reviewed
- [ ] Stap 3: Dry-run cleanup reviewed
- [ ] Stap 4: Database backup gemaakt
- [ ] Stap 5: Cleanup uitgevoerd
- [ ] Stap 6: Backend normalization getest
- [ ] Stap 7: Code changes deployed
- [ ] Stap 8: Production verificatie gedaan
- [ ] Stap 9: Frontend documentatie gedeeld
- [ ] Monitoring setup voor eerste week
- [ ] Success criteria gevalideerd

---

**Geschatte totale tijd:** 2-3 uur  
**Risico:** Laag (backward compatible, rollback mogelijk)  
**Impact:** Hoog (clean data voor frontend)

**Succes! 🚀**
