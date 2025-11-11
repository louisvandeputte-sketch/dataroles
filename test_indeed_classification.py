#!/usr/bin/env python3
"""Test Indeed job classification."""

from ingestion.job_title_classifier import classify_and_save
from database.client import db

print("Testing Indeed Job Classification")
print("=" * 80)

# Get an Indeed job without classification
result = db.client.table("job_postings")\
    .select("id, title, title_classification, source")\
    .eq("source", "indeed")\
    .is_("title_classification", "null")\
    .limit(1)\
    .execute()

if not result.data:
    print("\n❌ No unclassified Indeed jobs found")
    print("   All Indeed jobs are already classified!")
else:
    job = result.data[0]
    print(f"\nFound unclassified Indeed job:")
    print(f"  ID: {job['id']}")
    print(f"  Title: {job['title']}")
    print(f"  Classification: {job['title_classification']}")
    print(f"  Source: {job['source']}")
    
    print(f"\nAttempting to classify...")
    try:
        classification = classify_and_save(job['id'], job['title'])
        print(f"  ✅ Classification result: {classification}")
        
        # Verify in database
        updated = db.client.table("job_postings")\
            .select("title_classification")\
            .eq("id", job['id'])\
            .single()\
            .execute()
        
        print(f"  ✅ Database value: {updated.data['title_classification']}")
        
    except Exception as e:
        print(f"  ❌ Classification failed: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
