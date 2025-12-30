# Frontend Instructies: Time Ago Kolommen

## Overzicht
De database view `vw_job_listings` heeft nu 3 nieuwe kolommen die een tijdsaanduiding geven voor wanneer een job gepost werd:
- `time_ago_nl` - Nederlands
- `time_ago_fr` - Frans  
- `time_ago_en` - Engels

## Database Kolommen

### Beschikbare Kolommen
Alle drie kolommen zijn nu beschikbaar in de `vw_job_listings` view:

```sql
SELECT 
    job_posting_id,
    title,
    company_name,
    posted_date,
    posted_date_corrected,
    time_ago_nl,    -- NIEUW
    time_ago_fr,    -- NIEUW
    time_ago_en     -- NIEUW
FROM vw_job_listings;
```

### Mogelijke Waarden

#### Nederlands (`time_ago_nl`)
- `"Nieuw"` - Jobs < 7 dagen oud
- `"7 dagen geleden"`, `"8 dagen geleden"`, etc. - Jobs 7-13 dagen oud
- `"2 weken geleden"`, `"3 weken geleden"`, etc. - Jobs 14-29 dagen oud
- `"meer dan 1 maand geleden"` - Jobs 30+ dagen oud

#### Frans (`time_ago_fr`)
- `"Nouveau"` - Jobs < 7 dagen oud
- `"il y a 7 jours"`, `"il y a 8 jours"`, etc. - Jobs 7-13 dagen oud
- `"il y a 2 semaines"`, `"il y a 3 semaines"`, etc. - Jobs 14-29 dagen oud
- `"il y a plus d'un mois"` - Jobs 30+ dagen oud

#### Engels (`time_ago_en`)
- `"New"` - Jobs < 7 dagen oud
- `"7 days ago"`, `"8 days ago"`, etc. - Jobs 7-13 dagen oud
- `"2 weeks ago"`, `"3 weeks ago"`, etc. - Jobs 14-29 dagen oud
- `"more than 1 month ago"` - Jobs 30+ dagen oud

## API Endpoints

### Huidige Situatie
De backend API endpoints gebruiken momenteel **NIET** de `vw_job_listings` view, maar de `job_postings` tabel direct.

**Belangrijk**: De `time_ago_*` kolommen zijn **alleen beschikbaar in `vw_job_listings`**, niet in `job_postings`.

### Optie 1: Backend Aanpassing Nodig (Aanbevolen)
Om de `time_ago_*` kolommen te gebruiken, moet de backend aangepast worden om `vw_job_listings` te gebruiken in plaats van `job_postings`.

**Huidige endpoint**: `GET /api/jobs/`
- Gebruikt: `job_postings` tabel
- Bevat NIET: `time_ago_nl`, `time_ago_fr`, `time_ago_en`

**Wat nodig is**:
De backend developer moet de query in `/web/api/jobs.py` aanpassen om `vw_job_listings` te gebruiken.

### Optie 2: Frontend Berekening (Tijdelijke Oplossing)
Als je niet wilt wachten op backend aanpassingen, kun je de tijdsaanduiding in de frontend berekenen op basis van `posted_date` of `posted_date_corrected`:

```javascript
function getTimeAgoNL(postedDate) {
    const now = new Date();
    const posted = new Date(postedDate);
    const daysAgo = Math.floor((now - posted) / (1000 * 60 * 60 * 24));
    
    if (daysAgo < 7) {
        return "Nieuw";
    } else if (daysAgo < 14) {
        return `${daysAgo} dagen geleden`;
    } else if (daysAgo < 30) {
        const weeksAgo = Math.floor(daysAgo / 7);
        return `${weeksAgo} weken geleden`;
    } else {
        return "meer dan 1 maand geleden";
    }
}
```

## Implementatie Voorbeelden

### React Component Voorbeeld
```jsx
function JobCard({ job }) {
    return (
        <div className="job-card">
            <h3>{job.title}</h3>
            <p className="company">{job.company_name}</p>
            
            {/* Gebruik time_ago_nl als het beschikbaar is */}
            <span className="time-badge">
                {job.time_ago_nl}
            </span>
            
            {/* Optioneel: Toon "Nieuw" badge met speciale styling */}
            {job.time_ago_nl === "Nieuw" && (
                <span className="badge badge-new">Nieuw</span>
            )}
        </div>
    );
}
```

### CSS Styling Suggestie
```css
.time-badge {
    font-size: 0.875rem;
    color: #6b7280;
    font-weight: 500;
}

.badge-new {
    background-color: #10b981;
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
}
```

### Meertalige Ondersteuning
Als je app meertalig is, gebruik dan de juiste kolom:

```javascript
function getTimeAgoColumn(language) {
    switch(language) {
        case 'nl': return 'time_ago_nl';
        case 'fr': return 'time_ago_fr';
        case 'en': return 'time_ago_en';
        default: return 'time_ago_nl';
    }
}

// In je component
const timeAgoField = getTimeAgoColumn(currentLanguage);
const timeAgo = job[timeAgoField];
```

## Testen

### Test Query (Supabase)
```sql
-- Test of de kolommen data bevatten
SELECT 
    job_posting_id,
    title,
    time_ago_nl,
    time_ago_fr,
    time_ago_en
FROM vw_job_listings
LIMIT 10;
```

### API Test
Als de backend is aangepast om `vw_job_listings` te gebruiken:

```bash
curl http://localhost:8000/api/jobs/?limit=5
```

Verwachte response (voorbeeld):
```json
{
    "jobs": [
        {
            "job_posting_id": "abc-123",
            "title": "Data Engineer",
            "company_name": "TechCorp",
            "time_ago_nl": "Nieuw",
            "time_ago_fr": "Nouveau",
            "time_ago_en": "New"
        }
    ]
}
```

## Veelgestelde Vragen

**Q: Waarom zie ik de `time_ago_*` kolommen niet in de API response?**
A: De backend gebruikt momenteel `job_postings` in plaats van `vw_job_listings`. Vraag de backend developer om de query aan te passen.

**Q: Kan ik deze kolommen gebruiken voor filtering?**
A: Ja, maar alleen als je direct op `vw_job_listings` query't. Bijvoorbeeld:
```sql
SELECT * FROM vw_job_listings WHERE time_ago_nl = 'Nieuw';
```

**Q: Worden deze waarden automatisch bijgewerkt?**
A: Ja! De waarden worden dynamisch berekend bij elke query op basis van `NOW()` en `posted_date_corrected`.

**Q: Wat als `posted_date_corrected` NULL is?**
A: De CASE statement gebruikt `LEAST(js.first_seen_at, j.posted_date)`, dus er zal altijd een waarde zijn zolang er een posted_date is.

## Volgende Stappen

1. **Backend Developer**: Pas `/web/api/jobs.py` aan om `vw_job_listings` te gebruiken
2. **Frontend Developer**: Gebruik `time_ago_nl` (of `time_ago_fr`/`time_ago_en`) in de UI
3. **Test**: Verifieer dat de waarden correct worden weergegeven
4. **Styling**: Voeg speciale styling toe voor "Nieuw" jobs

## Contact
Voor vragen over deze implementatie, neem contact op met de backend developer of database administrator.
