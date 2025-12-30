#!/usr/bin/env python3
"""Check if the job has a description."""

from database.client import db

job_id = "463af755-466b-441f-b355-4097c619bb29"

print(f"Checking job description for: {job_id}\n")

# Get job description
result = db.client.table("job_descriptions")\
    .select("full_description_text")\
    .eq("job_posting_id", job_id)\
    .maybe_single()\
    .execute()

if result.data:
    desc = result.data.get("full_description_text")
    if desc:
        print(f"✅ Description exists: {len(desc)} characters")
        print(f"\nFirst 200 chars:\n{desc[:200]}")
    else:
        print("❌ Description field is NULL")
else:
    print("❌ No job_descriptions record found")
    print("\nThis is why enrichment fails!")
    print("The job needs a description before it can be enriched.")
