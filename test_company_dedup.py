#!/usr/bin/env python3
"""Test company deduplication logic."""

from database.client import db

print("Testing Company Deduplication Logic")
print("=" * 80)

# Test get_company_by_name
test_name = "AE"

print(f"\n🔍 Testing get_company_by_name('{test_name}')...")

result = db.get_company_by_name(test_name)

if result:
    print(f"✅ Found company:")
    print(f"  ID: {result['id']}")
    print(f"  Name: {result['name']}")
    print(f"  LinkedIn ID: {result.get('linkedin_company_id', 'None')}")
    print(f"  Has logo_data: {bool(result.get('logo_data'))}")
    print(f"  Has logo_url: {bool(result.get('logo_url'))}")
else:
    print(f"❌ No company found with name '{test_name}'")

# Test with a company that should have duplicates (if any remain)
print(f"\n🔍 Checking for any remaining duplicates...")

all_companies = db.client.table("companies")\
    .select("name")\
    .execute()

from collections import Counter
name_counts = Counter([c['name'] for c in all_companies.data])
duplicates = {name: count for name, count in name_counts.items() if count > 1}

if duplicates:
    print(f"⚠️  Found {len(duplicates)} names with duplicates:")
    for name, count in list(duplicates.items())[:5]:
        print(f"  • {name}: {count} entries")
        
        # Test get_company_by_name returns best one
        result = db.get_company_by_name(name)
        has_logo = bool(result.get('logo_data'))
        has_linkedin = bool(result.get('linkedin_company_id'))
        print(f"    → get_company_by_name returns: logo={has_logo}, linkedin={has_linkedin}")
else:
    print(f"✅ No duplicates found!")

print(f"\n" + "=" * 80)
print(f"✅ Deduplication logic test complete!")
print(f"\nNext: Run a scrape to test that new Indeed jobs reuse existing companies")
