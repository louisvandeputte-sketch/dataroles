#!/usr/bin/env python3
"""Test script to check if Tableau ecosystem is returned by the API."""

from database import db

# Test direct database query
print("🔍 Testing direct database query for Tableau ecosystem...\n")

ecosystems = db.get_all_ecosystems(active_only=True)
print(f"Total ecosystems returned: {len(ecosystems)}")

tableau_found = False
for eco in ecosystems:
    if 'tableau' in eco.get('name', '').lower():
        tableau_found = True
        print(f"\n✅ Found Tableau ecosystem:")
        print(f"   ID: {eco.get('id')}")
        print(f"   Name: {eco.get('name')}")
        print(f"   Display Name: {eco.get('display_name')}")
        print(f"   Is Active: {eco.get('is_active')}")
        print(f"   Relevance Score: {eco.get('relevance_score')}")
        print(f"   Category: {eco.get('category')}")

if not tableau_found:
    print("\n❌ Tableau ecosystem NOT found in API response")
    print("\nShowing first 10 ecosystems:")
    for i, eco in enumerate(ecosystems[:10]):
        print(f"   {i+1}. {eco.get('name')} (active: {eco.get('is_active')})")

print("\n" + "="*80)
print("Testing raw SQL query...")
print("="*80)

# Test raw SQL query
result = db.client.table("ecosystems")\
    .select("*")\
    .eq("name", "Tableau")\
    .eq("is_active", True)\
    .execute()

if result.data:
    print(f"\n✅ Tableau found via direct SQL query:")
    for eco in result.data:
        print(f"   ID: {eco.get('id')}")
        print(f"   Name: {eco.get('name')}")
        print(f"   Display Name: {eco.get('display_name')}")
        print(f"   Is Active: {eco.get('is_active')}")
else:
    print("\n❌ Tableau NOT found via direct SQL query")
