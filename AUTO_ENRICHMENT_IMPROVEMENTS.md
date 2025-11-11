# Auto-Enrichment Service Verbeteringen

## Huidig Probleem

De auto-enrichment service slaat locations met errors permanent over:
- Locations die gefaald zijn door quota errors worden NOOIT opnieuw geprobeerd
- Er is geen automatische retry logica
- Handmatige interventie is nodig om errors te clearen

## Voorgestelde Verbeteringen

### 1. **Automatic Error Retry**

Pas `auto_enrich_service.py` aan om errors na X tijd opnieuw te proberen:

```python
async def process_pending_locations(self):
    """Process locations that need enrichment."""
    try:
        # Find unenriched locations OR locations with old errors (>24h)
        one_day_ago = (datetime.utcnow() - timedelta(days=1)).isoformat()
        
        result = db.client.table("locations")\
            .select("id, city, country_code, region, ai_enrichment_error, ai_enriched_at")\
            .or_(
                f"ai_enriched.is.null,"
                f"ai_enriched.eq.false,"
                f"and(ai_enrichment_error.not.is.null,ai_enriched_at.lt.{one_day_ago})"
            )\
            .limit(10)\
            .execute()
```

### 2. **Exponential Backoff**

Track retry attempts en gebruik exponential backoff:

```python
# Add to locations table:
ALTER TABLE locations 
ADD COLUMN enrichment_retry_count INTEGER DEFAULT 0,
ADD COLUMN enrichment_next_retry_at TIMESTAMPTZ;

# In code:
if enrichment_retry_count >= 3:
    # Skip after 3 failed attempts
    continue

# Calculate next retry time with exponential backoff
retry_delay = 2 ** enrichment_retry_count  # 1h, 2h, 4h, 8h...
next_retry = now + timedelta(hours=retry_delay)
```

### 3. **Error Type Handling**

Verschillende retry strategieën voor verschillende error types:

```python
def should_retry_error(error_message: str, retry_count: int) -> bool:
    """Determine if error should be retried."""
    
    # Quota errors: retry after 24h, max 5 attempts
    if "quota" in error_message.lower():
        return retry_count < 5
    
    # Parsing errors: don't retry (likely permanent)
    if "parse" in error_message.lower() or "json" in error_message.lower():
        return False
    
    # Timeout errors: retry after 1h, max 3 attempts
    if "timeout" in error_message.lower():
        return retry_count < 3
    
    # Unknown errors: retry once
    return retry_count < 1
```

### 4. **Monitoring & Alerts**

Track enrichment health:

```python
# Daily summary
SELECT 
    COUNT(*) FILTER (WHERE ai_enriched = true) as enriched,
    COUNT(*) FILTER (WHERE ai_enrichment_error IS NOT NULL) as failed,
    COUNT(*) FILTER (WHERE ai_enriched IS NULL OR ai_enriched = false) as pending
FROM locations;

# Error breakdown
SELECT 
    CASE 
        WHEN ai_enrichment_error LIKE '%quota%' THEN 'Quota Exceeded'
        WHEN ai_enrichment_error LIKE '%timeout%' THEN 'Timeout'
        ELSE 'Other'
    END as error_type,
    COUNT(*) as count
FROM locations
WHERE ai_enrichment_error IS NOT NULL
GROUP BY error_type;
```

## Implementatie Plan

1. **Korte termijn** (nu):
   - Run `clear_location_errors.py` om huidige errors te clearen
   - Auto-enrichment service zal ze automatisch oppakken

2. **Middellange termijn** (deze week):
   - Voeg retry logica toe aan auto-enrichment service
   - Implementeer 24h retry voor quota errors

3. **Lange termijn** (volgende sprint):
   - Voeg retry_count en next_retry_at kolommen toe
   - Implementeer exponential backoff
   - Voeg monitoring dashboard toe

## Gebruik

### Nu: Clear errors handmatig
```bash
python clear_location_errors.py
```

### Toekomst: Automatisch retry
- Service retried automatisch na 24h
- Max 5 retry attempts voor quota errors
- Exponential backoff voor andere errors
