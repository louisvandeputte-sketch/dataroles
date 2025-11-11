#!/usr/bin/env python3
"""Check for duplicate company names."""

from database.client import db
from collections import Counter

print("Company Name Duplicates Analysis")
print("=" * 80)

# Get all companies
companies = db.client.table("companies")\
    .select("id, name, linkedin_company_id")\
    .execute()

print(f"\n📊 Total companies: {len(companies.data)}")

# Count duplicates
name_counts = Counter([c['name'] for c in companies.data])
duplicates = {name: count for name, count in name_counts.items() if count > 1}

print(f"🔍 Duplicate names: {len(duplicates)}")

# Show top duplicates
if duplicates:
    print(f"\n🔝 Top 10 duplicate company names:")
    for name, count in sorted(duplicates.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  • '{name}': {count} entries")
        
        # Show details for this name
        same_name = [c for c in companies.data if c['name'] == name]
        for company in same_name[:3]:  # Show first 3
            linkedin_id = company.get('linkedin_company_id', 'None')
            print(f"    - ID: {company['id'][:20]}... | LinkedIn ID: {linkedin_id}")

# Check 'AE' specifically
print(f"\n🔎 Checking 'AE' specifically:")
ae_companies = db.client.table("companies")\
    .select("id, name, linkedin_company_id, industry")\
    .eq("name", "AE")\
    .execute()

if ae_companies.data:
    print(f"  Found {len(ae_companies.data)} companies named 'AE':")
    for company in ae_companies.data:
        # Count jobs for this company
        jobs = db.client.table("job_postings")\
            .select("id, title", count="exact")\
            .eq("company_id", company['id'])\
            .execute()
        
        print(f"\n  Company ID: {company['id']}")
        print(f"  LinkedIn ID: {company.get('linkedin_company_id', 'None')}")
        print(f"  Industry: {company.get('industry', 'None')}")
        print(f"  Jobs: {jobs.count}")
        
        if jobs.data:
            print(f"  Sample jobs:")
            for job in jobs.data[:3]:
                print(f"    - {job['title'][:60]}")

print("\n" + "=" * 80)
print("\n💡 Explanation:")
print("  Companies are linked to jobs via company_id (UUID)")
print("  Company names are NOT unique - same name can have multiple IDs")
print("  This happens when:")
print("    1. Different LinkedIn company IDs have same name")
print("    2. Indeed jobs create separate company entries")
print("    3. Company name variations (e.g., 'AE' vs 'AE Group')")
