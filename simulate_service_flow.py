#!/usr/bin/env python3
"""Simulate the exact flow of auto-enrichment service for this specific job."""

from database.client import db

job_id = "463af755-466b-441f-b355-4097c619bb29"
job_title = "HR Strategy, Workforce & People Analytics Director"

print("=== SIMULATING AUTO-ENRICHMENT SERVICE FLOW ===\n")

# Step 1: Get all Data jobs (like service does)
print("Step 1: Fetching Data jobs (limit 500, sorted by posted_date DESC)...")
all_data_jobs = db.client.table("job_postings")\
    .select("id, title")\
    .eq("title_classification", "Data")\
    .eq("is_active", True)\
    .order("posted_date", desc=True)\
    .limit(500)\
    .execute()

print(f"  Found {len(all_data_jobs.data)} Data jobs")

# Check if our job is in the list
our_job_in_list = any(j['id'] == job_id for j in all_data_jobs.data)
print(f"  Our job in list: {our_job_in_list}")

# Step 2: Get enriched job IDs
print("\nStep 2: Fetching enriched job IDs...")
enriched = db.client.table("llm_enrichment")\
    .select("job_posting_id")\
    .not_.is_("enrichment_completed_at", "null")\
    .execute()

print(f"  Found {len(enriched.data)} enriched jobs")

enriched_ids = {e["job_posting_id"] for e in enriched.data}
our_job_enriched = job_id in enriched_ids
print(f"  Our job in enriched_ids: {our_job_enriched}")

# Step 3: Filter to unenriched jobs
print("\nStep 3: Filtering to unenriched jobs...")
jobs = []
for job in all_data_jobs.data:
    if job["id"] not in enriched_ids:
        jobs.append({"id": job["id"], "title": job["title"]})
        if len(jobs) >= 30:
            break

print(f"  Found {len(jobs)} unenriched jobs in batch")

# Check if our job is in the batch
our_job_in_batch = any(j['id'] == job_id for j in jobs)
print(f"  Our job in batch: {our_job_in_batch}")

if our_job_in_batch:
    position = next(i for i, j in enumerate(jobs) if j['id'] == job_id) + 1
    print(f"  Position in batch: {position}")

# Step 4: Show what would happen
print("\n=== WHAT WOULD HAPPEN ===")

if not our_job_in_list:
    print("❌ Job NOT in query results (not in first 500 by posted_date)")
elif our_job_enriched:
    print("❌ Job marked as enriched (would be skipped)")
elif not our_job_in_batch:
    print("⚠️  Job is unenriched but NOT in first 30 of batch")
    print(f"   There are {len([j for j in all_data_jobs.data if j['id'] not in enriched_ids])} unenriched jobs total")
    print(f"   Service only processes first 30 per cycle")
else:
    print(f"✅ Job WOULD be processed (position {position} in batch)")

# Step 5: Check the actual enrichment record status
print("\n=== ENRICHMENT RECORD DETAILS ===")
enrichment = db.client.table("llm_enrichment")\
    .select("*")\
    .eq("job_posting_id", job_id)\
    .maybe_single()\
    .execute()

if enrichment.data:
    e = enrichment.data
    print(f"Record exists: YES")
    print(f"Created at: {e.get('created_at')}")
    print(f"Completed at: {e.get('enrichment_completed_at')}")
    print(f"Error: {e.get('enrichment_error')}")
    
    if not e.get('enrichment_completed_at') and not e.get('enrichment_error'):
        print("\n🚨 STUCK ENRICHMENT DETECTED!")
        print("Record was created but never completed and has no error.")
        print("This job is in a 'pending' state and blocks new enrichment attempts.")
else:
    print("Record exists: NO")

# Step 6: Count total unenriched jobs
print("\n=== TOTAL UNENRICHED JOBS ===")
all_unenriched = [j for j in all_data_jobs.data if j['id'] not in enriched_ids]
print(f"Total unenriched in query (500): {len(all_unenriched)}")

if len(all_unenriched) > 30:
    print(f"\n⚠️  WARNING: {len(all_unenriched)} jobs waiting, but only 30 processed per cycle")
    print(f"   At 1 minute per cycle, this will take {len(all_unenriched)/30:.0f} minutes")
    print(f"   Our job position in queue: {next((i for i, j in enumerate(all_unenriched) if j['id'] == job_id), -1) + 1}")
