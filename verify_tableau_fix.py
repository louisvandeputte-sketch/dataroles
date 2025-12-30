#!/usr/bin/env python3
"""Verify that Tableau ecosystem is now returned after limit fix."""

import sys
import importlib

# Force reload of database module to pick up changes
if 'database' in sys.modules:
    del sys.modules['database']
if 'database.client' in sys.modules:
    del sys.modules['database.client']

from database import db

print("🔍 Testing after limit fix...\n")

# Count total
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
    print(f"\n✅ SUCCESS! Tableau found in results!")
    print(f"   ID: {tableau_found[0].get('id')}")
    print(f"   Name: {tableau_found[0].get('name')}")
    print(f"   Display Name: {tableau_found[0].get('display_name')}")
    print(f"   Relevance Score: {tableau_found[0].get('relevance_score')}")
else:
    print(f"\n❌ FAILED: Tableau NOT found in results")
    print(f"\nShowing ecosystems starting with 'T':")
    t_ecosystems = [eco for eco in ecosystems if eco.get('name', '').startswith('T')]
    for eco in t_ecosystems[:20]:
        print(f"   - {eco.get('name')}")
