#!/usr/bin/env python3
"""Check LinkedIn Company IDs in the database."""

from database.client import get_supabase_client

client = get_supabase_client()

# Get sample companies with their LinkedIn IDs
result = client.table("companies")\
    .select("id, name, linkedin_company_id")\
    .limit(10)\
    .execute()

print("Sample LinkedIn Company IDs in database:\n")
print(f"{'Name':<30} {'LinkedIn Company ID':<30}")
print("-" * 60)

for company in result.data:
    name = company.get('name', 'N/A')[:28]
    linkedin_id = company.get('linkedin_company_id') or 'NULL'
    print(f"{name:<30} {linkedin_id:<30}")

print(f"\nTotal companies checked: {len(result.data)}")

# Check specific IDs from the CSV
test_ids = ['48256', '76595890', '500621', '481244', '5004290', '12009057']
print("\n\nChecking specific IDs from your CSV:")
print("-" * 60)

for test_id in test_ids:
    result = client.table("companies")\
        .select("id, name, linkedin_company_id")\
        .eq("linkedin_company_id", test_id)\
        .execute()
    
    if result.data:
        print(f"✓ Found: {test_id} -> {result.data[0]['name']}")
    else:
        print(f"✗ NOT FOUND: {test_id}")
