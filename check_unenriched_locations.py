#!/usr/bin/env python3
"""Check why locations are not enriched."""

from database.client import db

# List of locations from the user's list
location_names = [
    "Arendonk", "Arlon", "Arrondissement of Aalst", "Arrondissement of Ghent",
    "Bierbeek", "Courcelles", "Deerlijk", "Deinze", "Destelbergen",
    "Erembodegem", "Evergem", "Kuurne", "Luxemburg", "Oostende",
    "Ronse", "Rotselaar", "Sint-Gillis", "Ukkel"
]

print("🔍 Checking Location Enrichment Status")
print("=" * 80)

for city_name in location_names:
    # Find location
    result = db.client.table("locations")\
        .select("id, city, ai_enriched, ai_enrichment_error, ai_enriched_at")\
        .ilike("city", city_name)\
        .execute()
    
    if result.data:
        for location in result.data:
            city = location.get("city")
            enriched = location.get("ai_enriched")
            error = location.get("ai_enrichment_error")
            enriched_at = location.get("ai_enriched_at")
            
            print(f"\n📍 {city}")
            print(f"   Enriched: {enriched}")
            
            if error:
                print(f"   ❌ Error: {error[:100]}...")
                print(f"   Attempted at: {enriched_at}")
            elif enriched:
                print(f"   ✅ Enriched at: {enriched_at}")
            else:
                print(f"   ⏳ Not yet enriched (no error)")
    else:
        print(f"\n❓ {city_name} - NOT FOUND in database")

print("\n" + "=" * 80)
print("\n📊 Summary:")

# Get counts
all_locations = db.client.table("locations")\
    .select("id, ai_enriched, ai_enrichment_error")\
    .execute()

if all_locations.data:
    total = len(all_locations.data)
    enriched = sum(1 for loc in all_locations.data if loc.get("ai_enriched"))
    with_errors = sum(1 for loc in all_locations.data if loc.get("ai_enrichment_error"))
    pending = total - enriched - with_errors
    
    print(f"Total locations: {total}")
    print(f"✅ Enriched: {enriched}")
    print(f"❌ With errors: {with_errors}")
    print(f"⏳ Pending (no error): {pending}")
    
    if with_errors > 0:
        print(f"\n⚠️ {with_errors} locations have errors and won't be auto-enriched!")
        print("   These need manual retry or error clearing.")
