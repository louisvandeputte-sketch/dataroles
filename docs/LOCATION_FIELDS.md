# Location Fields in vw_job_listings

## 📍 Quick Reference for Frontend Developers

All location data is available in the `vw_job_listings` view. Here's what you need to know:

---

## City Names (Multilingual)

Display the city name in the user's language:

```javascript
job.city_name_nl  // "Brussel", "Antwerpen", "Gent"
job.city_name_en  // "Brussels", "Antwerp", "Ghent"
job.city_name_fr  // "Bruxelles", "Anvers", "Gand"
```

**Fallback:** If `null`, use `job.city_official_name`

---

## Region/Province (Multilingual)

```javascript
job.subdivision_name_nl  // "Vlaams-Brabant", "Oost-Vlaanderen"
job.subdivision_name_en  // "Flemish Brabant", "East Flanders"
job.subdivision_name_fr  // "Brabant flamand", "Flandre-Orientale"
```

---

## Country (Multilingual)

```javascript
job.country_name_nl  // "België", "Nederland"
job.country_name_en  // "Belgium", "Netherlands"
job.country_name_fr  // "Belgique", "Pays-Bas"
```

**Country Code:**
```javascript
job.country_code_3  // "BEL", "NLD", "FRA" (ISO 3166-1 alpha-3)
```

---

## Geographic Coordinates

For map visualization and proximity features:

```javascript
job.longitude  // e.g., 4.9041 (range: -180 to 180)
job.latitude   // e.g., 52.3676 (range: -90 to 90)
```

### Example - Display on Map

**Leaflet:**
```javascript
if (job.latitude && job.longitude) {
  L.marker([job.latitude, job.longitude])
    .bindPopup(`<b>${job.title}</b><br>${job.company_name}`)
    .addTo(map);
}
```

**Google Maps:**
```javascript
new google.maps.Marker({
  position: { lat: job.latitude, lng: job.longitude },
  map: map,
  title: job.title
});
```

**Mapbox:**
```javascript
new mapboxgl.Marker()
  .setLngLat([job.longitude, job.latitude])
  .setPopup(new mapboxgl.Popup().setHTML(`<h3>${job.title}</h3>`))
  .addTo(map);
```

---

## Timezone

For date/time localization:

```javascript
job.timezone  // "Europe/Brussels", "Europe/Amsterdam"

// Example with moment.js
const localTime = moment.utc(job.posted_date)
  .tz(job.timezone)
  .format('DD/MM/YYYY HH:mm');
```

---

## Common Use Cases

### 1. Display Full Location

```javascript
function getLocationString(job, language = 'en') {
  const city = job[`city_name_${language}`] || job.city_official_name;
  const country = job[`country_name_${language}`] || job.country_name;
  
  return `${city}, ${country}`;
}

// Usage
getLocationString(job, 'nl')  // "Brussel, België"
getLocationString(job, 'en')  // "Brussels, Belgium"
getLocationString(job, 'fr')  // "Bruxelles, Belgique"
```

### 2. Display with Region

```javascript
function getFullLocation(job, language = 'en') {
  const city = job[`city_name_${language}`] || job.city_official_name;
  const region = job[`subdivision_name_${language}`];
  const country = job[`country_name_${language}`] || job.country_name;
  
  if (region) {
    return `${city}, ${region}, ${country}`;
  }
  return `${city}, ${country}`;
}
```

### 3. Calculate Distance

```javascript
function getDistance(lat1, lon1, lat2, lon2) {
  // Haversine formula (returns distance in km)
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = 
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  return R * c;
}

// Filter jobs within 50km
const nearbyJobs = jobs.filter(job => {
  if (!job.latitude || !job.longitude) return false;
  const distance = getDistance(
    userLat, userLon,
    job.latitude, job.longitude
  );
  return distance <= 50;
});
```

### 4. Group by City

```javascript
const jobsByCity = jobs.reduce((groups, job) => {
  const city = job.city_name_en || job.city_official_name;
  if (!groups[city]) {
    groups[city] = [];
  }
  groups[city].push(job);
  return groups;
}, {});
```

---

## Complete Field List

| Field | Type | Description |
|-------|------|-------------|
| `city_name_nl` | TEXT | City in Dutch |
| `city_name_en` | TEXT | City in English |
| `city_name_fr` | TEXT | City in French |
| `subdivision_name_nl` | TEXT | Region in Dutch |
| `subdivision_name_en` | TEXT | Region in English |
| `subdivision_name_fr` | TEXT | Region in French |
| `country_name_nl` | TEXT | Country in Dutch |
| `country_name_en` | TEXT | Country in English |
| `country_name_fr` | TEXT | Country in French |
| `longitude` | DECIMAL | Longitude (-180 to 180) |
| `latitude` | DECIMAL | Latitude (-90 to 90) |
| `country_code_3` | TEXT | ISO alpha-3 code |
| `timezone` | TEXT | IANA timezone |
| `city_official_name` | TEXT | Official city name |
| `country_name` | TEXT | Country (local language) |
| `location_id` | UUID | Location record ID |

---

## Important Notes

### Null Values
Some fields may be `null`:
- **Coordinates:** Not all locations are geocoded yet (automatic process runs every 6 hours)
- **Multilingual names:** Older locations may not have AI-enriched translations

**Always provide fallbacks:**
```javascript
const city = job.city_name_en || job.city_official_name || 'Unknown';
```

### Location Override
The view automatically handles vague locations:
- If a job has a vague location (e.g., "Flemish Region"), it uses a more specific city from company data
- **You don't need to handle this** - the view already returns the correct location

### Coordinate Precision
- Coordinates have 7 decimal places (~1cm precision)
- For display: round to 4 decimals
- For calculations: use full precision

---

## Example Supabase Query

```javascript
const { data: jobs } = await supabase
  .from('vw_job_listings')
  .select(`
    job_posting_id,
    title,
    company_name,
    city_name_en,
    country_name_en,
    longitude,
    latitude,
    timezone
  `)
  .not('latitude', 'is', null)  // Only jobs with coordinates
  .limit(100);
```

---

## Questions?

Contact the backend team if you need:
- Additional location fields
- Different coordinate formats
- Custom location queries
