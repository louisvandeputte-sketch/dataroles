#!/usr/bin/env python3
"""Check geocoding statistics"""

from database.client import db

# Count total locations
total = db.client.table("locations").select("id", count="exact").execute()
print(f"\n📊 Total locations: {total.count}")

# Count locations WITH coordinates
with_coords = db.client.table("locations")\
    .select("id", count="exact")\
    .not_.is_("latitude", "null")\
    .not_.is_("longitude", "null")\
    .execute()
print(f"✅ With coordinates: {with_coords.count}")

# Count locations WITHOUT coordinates
without_coords = db.client.table("locations")\
    .select("id", count="exact")\
    .or_("latitude.is.null,longitude.is.null")\
    .execute()
print(f"❌ Without coordinates: {without_coords.count}")

# Check if geocoding service is running
print(f"\n📍 Coverage: {with_coords.count / total.count * 100:.1f}%")

# Check coordinates_enriched flag
enriched = db.client.table("locations")\
    .select("id", count="exact")\
    .eq("coordinates_enriched", True)\
    .execute()
print(f"\n🏷️ Marked as enriched: {enriched.count}")

# Sample locations without coordinates
print("\n🔍 Sample locations without coordinates:")
samples = db.client.table("locations")\
    .select("id, city, country_name, full_location_string")\
    .is_("latitude", "null")\
    .limit(10)\
    .execute()

for loc in samples.data:
    print(f"   - {loc.get('city')} ({loc.get('country_name')}) - {loc.get('full_location_string')}")
