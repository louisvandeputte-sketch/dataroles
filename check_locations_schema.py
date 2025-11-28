#!/usr/bin/env python3
"""Check locations table schema and data"""

from database.client import db

# Check if longitude/latitude columns exist
result = db.client.table("locations")\
    .select("*")\
    .limit(5)\
    .execute()

if result.data:
    print("\n📊 Locations table columns:")
    print(f"   Columns: {list(result.data[0].keys())}")
    
    print("\n🔍 First 5 locations:")
    for loc in result.data:
        print(f"\n   ID: {loc.get('id')}")
        print(f"   Name: {loc.get('name')}")
        print(f"   City: {loc.get('city')}")
        print(f"   Country: {loc.get('country')}")
        print(f"   Latitude: {loc.get('latitude', 'MISSING')}")
        print(f"   Longitude: {loc.get('longitude', 'MISSING')}")
else:
    print("❌ No locations found")
