# Job Title Classification Script

## Overzicht

Dit script classificeert alle job titels in de database als "Data" (data-gerelateerd) of "NIS" (Not In Scope / niet data-gerelateerd) met behulp van een LLM.

## Gebruik

```bash
cd /Users/louisvandeputte/datarole
source venv/bin/activate
python scripts/classify_job_titles.py
```

## Wat doet het?

1. **Toont initiële statistieken:**
   - Totaal aantal jobs
   - Aantal al geclassificeerd als "Data"
   - Aantal al geclassificeerd als "NIS"
   - Aantal nog niet geclassificeerd

2. **Classificeert jobs in batches:**
   - Verwerkt 50 jobs per batch (voor betrouwbaarheid)
   - Toont progress tijdens verwerking
   - Stopt automatisch als alle jobs geclassificeerd zijn

3. **Toont finale statistieken:**
   - Percentage "Data" vs "NIS" jobs
   - Totaal aantal geclassificeerde jobs

## LLM Prompt Details

- **Prompt ID:** `pmpt_690724c8e4f48190a9d249a76325af9d056897bd40d5b2a3`
- **Versie:** 2
- **Logica:** Inclusief - bij twijfel wordt "Data" gekozen
- **Output:** Enkel "Data" of "NIS" (geen JSON, geen uitleg)

## Automatische Classificatie

**Nieuwe jobs worden automatisch geclassificeerd** tijdens het scraping proces:
- Gebeurt in `process_job_posting()` (Step 8)
- Non-blocking: faalt de job processing niet
- Resultaat direct zichtbaar in de frontend

## Frontend Weergave

In de jobs database tabel verschijnt een "Title Check" kolom met:
- 🟢 **Groene badge** voor "Data" jobs
- ⚫ **Grijze badge** voor "NIS" jobs
- 🟡 **Gele badge** voor "Pending" (nog niet geclassificeerd)

## Wanneer uitvoeren?

- **Eenmalig:** Na het toevoegen van de feature (voor bestaande jobs)
- **Optioneel:** Als je vermoedt dat er jobs zijn zonder classificatie
- **Niet nodig:** Voor nieuwe jobs (worden automatisch geclassificeerd)

## Performance

- ~50 jobs per minuut (afhankelijk van OpenAI API snelheid)
- Voor 1000 jobs: ~20 minuten
- Gebruikt batching om API rate limits te respecteren
