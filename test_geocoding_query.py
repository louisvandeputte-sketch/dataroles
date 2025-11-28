#!/usr/bin/env python3
"""Test the geocoding query"""

from database.client import db

# Test the query
query = db.client.table("locations")\
    .select("id, city_name_en, country_name_en, city_official_name, country_name, longitude, latitude, coordinates_enriched")

# Filter locations without coordinates (NULL or false)
query = query.or_("coordinates_enriched.is.null,coordinates_enriched.eq.false")

# Only select locations that have city and country data
query = query.not_.is_("city_name_en", "null").not_.is_("country_name_en", "null")

query = query.limit(10)

# Fetch locations
response = query.execute()
locations = response.data

print(f"\n📍 Found {len(locations)} locations to geocode:")
for loc in locations:
    print(f"\n   ID: {loc['id']}")
    print(f"   City: {loc.get('city_name_en')} ({loc.get('city_official_name')})")
    print(f"   Country: {loc.get('country_name_en')} ({loc.get('country_name')})")
    print(f"   Coords: ({loc.get('longitude')}, {loc.get('latitude')})")
    print(f"   Enriched: {loc.get('coordinates_enriched')}")
