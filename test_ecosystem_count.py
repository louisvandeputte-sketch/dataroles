#!/usr/bin/env python3
"""Test script to count total ecosystems in database."""

from database import db

# Count total ecosystems
print("🔍 Counting ecosystems in database...\n")

# Get all active ecosystems
result = db.client.table("ecosystems")\
    .select("*", count="exact")\
    .eq("is_active", True)\
    .execute()

print(f"Total active ecosystems in database: {result.count}")

# Test with new limit
ecosystems = db.get_all_ecosystems(active_only=True)
print(f"Ecosystems returned by get_all_ecosystems(): {len(ecosystems)}")

# Check if Tableau is in the list
tableau_found = [eco for eco in ecosystems if eco.get('name') == 'Tableau']
if tableau_found:
    print(f"\n✅ Tableau found in results!")
    print(f"   ID: {tableau_found[0].get('id')}")
    print(f"   Name: {tableau_found[0].get('name')}")
    print(f"   Display Name: {tableau_found[0].get('display_name')}")
else:
    print(f"\n❌ Tableau NOT found in results")
    print(f"\nLast 10 ecosystems (alphabetically):")
    for eco in ecosystems[-10:]:
        print(f"   - {eco.get('name')}")
