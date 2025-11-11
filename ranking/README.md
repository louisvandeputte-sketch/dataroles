# Job Ranking System

Automatisch ranking systeem voor job vacatures op basis van meerdere criteria.

## Overzicht

Het ranking systeem berekent een score voor elke actieve job vacature op basis van:

### Scoring Criteria (Weights)

1. **Versheid & Actualiteit (25%)**
   - < 1 dag oud: 100 punten
   - < 3 dagen: 90 punten
   - < 7 dagen: 75 punten
   - < 14 dagen: 60 punten
   - < 30 dagen: 40 punten
   - Ouder: 20 punten

2. **Kwaliteit van Informatie (20%)**
   - Skills gespecificeerd (≥3): 25 punten
   - Salaris range: 25 punten
   - Seniority level: 15 punten
   - Employment type: 10 punten
   - Lange samenvatting: 15 punten
   - Gedetailleerde beschrijving (>500 chars): 10 punten

3. **Transparantie & Directheid (20%)**
   - Direct werkgever (geen recruitment): 60 punten
   - Apply URL beschikbaar: 20 punten
   - Aantal applicants zichtbaar: 10 punten
   - Company logo: 10 punten

4. **Match met Data Roles (15%)**
   - Data Engineer, Data Scientist: 100 punten
   - Data Analyst, Analytics Engineer: 90 punten
   - ML Engineer, BI Developer: 85 punten
   - Andere data roles: 70 punten

5. **Volledigheid Profiel (10%)**
   - Employee count: 15 punten
   - Industry: 15 punten
   - Company URL: 15 punten
   - City: 15 punten
   - Function areas: 20 punten
   - AI enrichment completed: 20 punten

6. **Bedrijfsreputatie (10%)**
   - Company rating (≥4.5): 40 punten
   - Company size (large): 30 punten
   - FAANG bonus: 30 punten

### Diversity Modifiers

Om spreiding te garanderen:

- **Company penalty:** -15% per extra vacature van zelfde bedrijf
- **Role penalty:** -10% per extra vacature van zelfde role type
- **Seniority penalty:** -5% per extra vacature van zelfde seniority
- **Location boost:** +5% voor eerste vacature van een locatie

## Database Schema

### Nieuwe Kolommen in `job_postings`

```sql
ranking_score NUMERIC(10, 2)        -- Score 0-100
ranking_position INTEGER             -- Positie 1, 2, 3, ...
ranking_updated_at TIMESTAMPTZ       -- Laatste berekening
ranking_metadata JSONB               -- Score breakdown
```

### Metadata Structuur

```json
{
  "freshness_score": 90.0,
  "quality_score": 75.0,
  "transparency_score": 80.0,
  "role_match_score": 100.0,
  "completeness_score": 65.0,
  "reputation_score": 70.0,
  "base_score": 82.5,
  "company_rank": 1,
  "role_type_rank": 2,
  "location_rank": 1,
  "seniority_rank": 1
}
```

## Gebruik

### Automatische Berekening

Het systeem berekent rankings automatisch **elke nacht om 3:00 AM Belgische tijd**.

Start de scheduler:

```bash
python -m ranking.scheduler
```

### Handmatige Berekening

#### Via UI
1. Ga naar Jobs pagina
2. Klik op "Calculate Rankings" knop
3. Bevestig de actie
4. Rankings worden in background berekend

#### Via API
```bash
curl -X POST http://localhost:8000/api/ranking/calculate
```

#### Via Python
```python
from ranking.job_ranker import calculate_and_save_rankings

# Calculate and save rankings
num_ranked = calculate_and_save_rankings()
print(f"Ranked {num_ranked} jobs")
```

### Status Checken

```bash
curl http://localhost:8000/api/ranking/status
```

Response:
```json
{
  "status": "completed",
  "message": "Rankings are up to date",
  "last_updated": "2025-11-10T03:00:00Z",
  "jobs_ranked": 2083
}
```

## API Endpoints

### POST `/api/ranking/calculate`
Trigger handmatige ranking berekening (runs in background)

**Response:**
```json
{
  "status": "started",
  "message": "Ranking calculation started in background"
}
```

### GET `/api/ranking/status`
Krijg status van laatste ranking berekening

**Response:**
```json
{
  "status": "completed",
  "last_updated": "2025-11-10T03:00:00Z",
  "jobs_ranked": 2083
}
```

## Migratie

Run migratie 031 om ranking kolommen toe te voegen:

```bash
# In Supabase SQL Editor
psql $DATABASE_URL < database/migrations/031_add_ranking_score.sql
```

## Monitoring

Logs worden geschreven via `loguru`:

```
📊 Ranking 2083 active jobs...
✅ Ranking complete! 2083 jobs ranked.
💾 Saving rankings for 2083 jobs...
✅ Rankings saved to database
```

## Troubleshooting

### Rankings worden niet berekend
- Check of scheduler draait: `ps aux | grep scheduler`
- Check logs voor errors
- Verify database connectie

### Lage scores
- Check of AI enrichment is gedaan
- Verify company en location data
- Check posted_date is recent

### Geen diversity
- Verify diversity modifiers zijn actief
- Check company_rank en role_type_rank in metadata

## Development

### Test Ranking Logica

```python
from ranking.job_ranker import JobRankingSystem, load_jobs_from_database

# Load jobs
jobs = load_jobs_from_database()

# Rank
ranker = JobRankingSystem()
ranked_jobs = ranker.rank_jobs(jobs)

# Inspect top 10
for job in ranked_jobs[:10]:
    print(f"{job.final_rank}. {job.title} - Score: {job.final_score:.2f}")
```

### Adjust Weights

Edit `ranking/job_ranker.py`:

```python
class JobRankingSystem:
    WEIGHT_FRESHNESS = 0.25      # 25%
    WEIGHT_QUALITY = 0.20        # 20%
    WEIGHT_TRANSPARENCY = 0.20   # 20%
    WEIGHT_ROLE_MATCH = 0.15     # 15%
    WEIGHT_COMPLETENESS = 0.10   # 10%
    WEIGHT_REPUTATION = 0.10     # 10%
```

## Future Enhancements

- [ ] User feedback on rankings
- [ ] A/B testing different weights
- [ ] Machine learning based ranking
- [ ] Personalized rankings per user
- [ ] Ranking history tracking
