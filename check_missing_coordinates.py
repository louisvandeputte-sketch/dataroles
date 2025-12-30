"""Check how many locations are missing longitude/latitude coordinates."""

from database import db

print("="*80)
print("LOCATIONS MISSING COORDINATES")
print("="*80)

# Total locations
total = db.client.table("locations")\
    .select("id", count="exact")\
    .execute()

print(f"\nTotal locations: {total.count}")

# Locations with coordinates
with_coords = db.client.table("locations")\
    .select("id", count="exact")\
    .not_.is_("longitude", "null")\
    .not_.is_("latitude", "null")\
    .execute()

print(f"Locations with coordinates: {with_coords.count}")

# Locations without coordinates
missing = total.count - with_coords.count
print(f"Locations WITHOUT coordinates: {missing}")
print(f"Coverage: {(with_coords.count / total.count * 100):.1f}%")

# Get some examples of locations without coordinates
examples = db.client.table("locations")\
    .select("id, city_official_name, country_name, city_name_nl")\
    .is_("longitude", "null")\
    .limit(10)\
    .execute()

if examples.data:
    print(f"\nExamples of locations without coordinates:")
    for loc in examples.data:
        city = loc.get('city_official_name') or loc.get('city_name_nl') or 'Unknown'
        country = loc.get('country_name') or 'Unknown'
        print(f"  - {city}, {country}")

print("\n" + "="*80)
