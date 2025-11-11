#!/usr/bin/env python3
"""Classify all Indeed jobs."""

from ingestion.job_title_classifier import classify_and_save
from database.client import db
from loguru import logger

print("Classifying Indeed Jobs")
print("=" * 80)

# Get all Indeed jobs without classification
result = db.client.table("job_postings")\
    .select("id, title, source")\
    .eq("source", "indeed")\
    .is_("title_classification", "null")\
    .execute()

total = len(result.data)
print(f"\nFound {total} unclassified Indeed jobs")

if total == 0:
    print("✅ All Indeed jobs are already classified!")
else:
    print(f"\nClassifying...")
    
    classified = 0
    failed = 0
    
    for i, job in enumerate(result.data, 1):
        try:
            classification = classify_and_save(job['id'], job['title'])
            if classification:
                classified += 1
                print(f"  [{i}/{total}] ✅ {job['title'][:50]:50} → {classification}")
            else:
                failed += 1
                print(f"  [{i}/{total}] ❌ {job['title'][:50]:50} → Failed")
        except Exception as e:
            failed += 1
            print(f"  [{i}/{total}] ❌ {job['title'][:50]:50} → Error: {e}")
    
    print(f"\n" + "=" * 80)
    print(f"Results:")
    print(f"  Classified: {classified}")
    print(f"  Failed: {failed}")
    print(f"  Total: {total}")
