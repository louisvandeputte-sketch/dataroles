#!/usr/bin/env python3
"""Test source filter in database."""

from database.client import db

print("Testing Source Filter")
print("=" * 80)

# Test 1: Count total jobs
print("\n1. Total jobs:")
all_jobs, total = db.search_jobs(limit=1, offset=0)
print(f"   Total: {total}")

# Test 2: Count LinkedIn jobs
print("\n2. LinkedIn jobs:")
linkedin_jobs, linkedin_total = db.search_jobs(source="linkedin", limit=1, offset=0)
print(f"   Total: {linkedin_total}")

# Test 3: Count Indeed jobs
print("\n3. Indeed jobs:")
indeed_jobs, indeed_total = db.search_jobs(source="indeed", limit=1, offset=0)
print(f"   Total: {indeed_total}")

# Test 4: Verify totals match
print("\n4. Verification:")
if linkedin_total + indeed_total == total:
    print(f"   ✅ Totals match: {linkedin_total} + {indeed_total} = {total}")
else:
    print(f"   ⚠️  Totals don't match: {linkedin_total} + {indeed_total} ≠ {total}")

# Test 5: Sample jobs from each source
print("\n5. Sample jobs:")
if linkedin_total > 0:
    linkedin_sample, _ = db.search_jobs(source="linkedin", limit=3, offset=0)
    print(f"\n   LinkedIn samples:")
    for job in linkedin_sample:
        print(f"   - {job['title']} at {job.get('companies', {}).get('name', 'N/A')} (source: {job.get('source')})")

if indeed_total > 0:
    indeed_sample, _ = db.search_jobs(source="indeed", limit=3, offset=0)
    print(f"\n   Indeed samples:")
    for job in indeed_sample:
        print(f"   - {job['title']} at {job.get('companies', {}).get('name', 'N/A')} (source: {job.get('source')})")

print("\n" + "=" * 80)
print("✅ Source filter test complete!")
