#!/usr/bin/env python3
"""Resolve duplicate dedup_keys before creating unique index."""

from database.client import db
from collections import Counter
from datetime import datetime

print("Resolving Duplicate dedup_keys")
print("=" * 80)

# 1. Find all duplicates
print("\n1. Finding duplicates...")

# Fetch ALL jobs (handle pagination)
all_jobs_data = []
offset = 0
batch_size = 1000

while True:
    batch = db.client.table("job_postings")\
        .select("id, dedup_key, created_at, source, linkedin_job_id, indeed_job_id")\
        .not_.is_("dedup_key", "null")\
        .range(offset, offset + batch_size - 1)\
        .execute()
    
    if not batch.data:
        break
    
    all_jobs_data.extend(batch.data)
    offset += batch_size
    
    if len(batch.data) < batch_size:
        break

print(f"   Loaded {len(all_jobs_data)} jobs")

# Create a mock result object
class MockResult:
    def __init__(self, data):
        self.data = data

all_jobs = MockResult(all_jobs_data)

# Count occurrences
key_counts = Counter([j['dedup_key'] for j in all_jobs.data])
duplicates = {k: v for k, v in key_counts.items() if v > 1}

print(f"   Found {len(duplicates)} duplicate dedup_keys")
print(f"   Total duplicate jobs: {sum(duplicates.values())}")

if not duplicates:
    print("\n✅ No duplicates found! You can create the unique index.")
    exit(0)

# 2. Show examples
print("\n2. Examples of duplicates:")
for key, count in list(duplicates.items())[:5]:
    print(f"   {key[:70]:70} → {count} jobs")

# 3. Resolution strategy
print("\n3. Resolution Strategy:")
print("   For each duplicate dedup_key:")
print("   - Keep the OLDEST job (earliest created_at)")
print("   - Merge sources from newer jobs into oldest")
print("   - Delete newer duplicate jobs")

proceed = input("\nProceed with resolution? (yes/no): ")
if proceed.lower() != 'yes':
    print("Aborted.")
    exit(0)

# 4. Resolve duplicates
print("\n4. Resolving duplicates...")

resolved_count = 0
merged_sources = 0
deleted_jobs = 0

for dedup_key, count in duplicates.items():
    # Get all jobs with this dedup_key
    jobs = [j for j in all_jobs.data if j['dedup_key'] == dedup_key]
    
    # Sort by created_at (oldest first)
    jobs.sort(key=lambda x: x['created_at'])
    
    # Keep the oldest
    keep_job = jobs[0]
    duplicate_jobs = jobs[1:]
    
    print(f"\n   Processing: {dedup_key[:60]}")
    print(f"     Keeping: {keep_job['id']} (created {keep_job['created_at'][:10]})")
    print(f"     Merging: {len(duplicate_jobs)} duplicates")
    
    # For each duplicate, merge its sources
    for dup_job in duplicate_jobs:
        # Get sources from duplicate job
        dup_sources = db.client.table("job_sources")\
            .select("source, source_job_id, first_seen_at")\
            .eq("job_posting_id", dup_job['id'])\
            .execute()
        
        # Add these sources to the kept job (if not already present)
        for source_entry in dup_sources.data:
            # Check if this source already exists for kept job
            existing = db.client.table("job_sources")\
                .select("id")\
                .eq("job_posting_id", keep_job['id'])\
                .eq("source", source_entry['source'])\
                .execute()
            
            if not existing.data:
                # Add source to kept job
                try:
                    db.client.table("job_sources").insert({
                        "job_posting_id": keep_job['id'],
                        "source": source_entry['source'],
                        "source_job_id": source_entry['source_job_id'],
                        "first_seen_at": source_entry['first_seen_at'],
                        "last_seen_at": datetime.now().isoformat()
                    }).execute()
                    merged_sources += 1
                    print(f"       ✅ Merged {source_entry['source']} source")
                except Exception as e:
                    print(f"       ⚠️  Could not merge source: {e}")
        
        # Delete the duplicate job (CASCADE will delete job_sources, job_type_assignments, etc.)
        try:
            db.client.table("job_postings")\
                .delete()\
                .eq("id", dup_job['id'])\
                .execute()
            deleted_jobs += 1
            print(f"       ✅ Deleted duplicate job {dup_job['id']}")
        except Exception as e:
            print(f"       ❌ Could not delete job: {e}")
    
    resolved_count += 1

print("\n" + "=" * 80)
print("Resolution Summary:")
print(f"  Duplicate groups resolved: {resolved_count}")
print(f"  Sources merged: {merged_sources}")
print(f"  Duplicate jobs deleted: {deleted_jobs}")

# 5. Verify no more duplicates
print("\n5. Verifying...")
remaining = db.client.table("job_postings")\
    .select("dedup_key")\
    .not_.is_("dedup_key", "null")\
    .execute()

remaining_counts = Counter([j['dedup_key'] for j in remaining.data])
remaining_dups = {k: v for k, v in remaining_counts.items() if v > 1}

if remaining_dups:
    print(f"   ⚠️  Still {len(remaining_dups)} duplicates remaining")
    print("   You may need to run this script again")
else:
    print(f"   ✅ No duplicates remaining!")
    print("\n   You can now create the unique index:")
    print("   CREATE UNIQUE INDEX idx_job_postings_dedup_key ON job_postings(dedup_key);")
