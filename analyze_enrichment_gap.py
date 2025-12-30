#!/usr/bin/env python3
"""Analyze the enrichment gap - why are 111 jobs showing as unenriched?"""

from database.client import db

print("=== ENRICHMENT GAP ANALYSIS ===\n")

# Method 1: Count from job_postings side
print("Method 1: From job_postings table")
all_data_jobs = db.client.table("job_postings")\
    .select("id", count="exact")\
    .eq("title_classification", "Data")\
    .execute()
print(f"Total Data jobs: {all_data_jobs.count}")

# Method 2: Count enrichment records
print("\nMethod 2: From llm_enrichment table")
all_enrichments = db.client.table("llm_enrichment")\
    .select("job_posting_id", count="exact")\
    .execute()
print(f"Total enrichment records: {all_enrichments.count}")

completed_enrichments = db.client.table("llm_enrichment")\
    .select("job_posting_id", count="exact")\
    .not_.is_("enrichment_completed_at", "null")\
    .execute()
print(f"Completed enrichments: {completed_enrichments.count}")

# Method 3: Join approach (what the UI uses)
print("\nMethod 3: Join approach (UI method)")
enriched_via_join = db.client.table("llm_enrichment")\
    .select("job_posting_id, job_postings!inner(title_classification)", count="exact")\
    .eq("job_postings.title_classification", "Data")\
    .not_.is_("enrichment_completed_at", "null")\
    .execute()
print(f"Enriched Data jobs (via join): {enriched_via_join.count}")

# The gap
gap = all_data_jobs.count - enriched_via_join.count
print(f"\n*** GAP: {gap} jobs ***")

# Find jobs that have enrichment records but don't show up in join
print("\n=== Finding the missing jobs ===")

# Get all Data job IDs
all_data_ids = {j["id"] for j in db.client.table("job_postings")
    .select("id")
    .eq("title_classification", "Data")
    .limit(3000)
    .execute().data}

# Get enriched job IDs via join
enriched_ids_join = {e["job_posting_id"] for e in enriched_via_join.data}

# Get all completed enrichment IDs (no join)
all_completed_ids = {e["job_posting_id"] for e in completed_enrichments.data}

# Find Data jobs with completed enrichment but not in join result
missing_from_join = all_completed_ids - enriched_ids_join
print(f"Jobs with completed enrichment but missing from join: {len(missing_from_join)}")

# Check if these are actually Data jobs
if missing_from_join:
    sample = list(missing_from_join)[:10]
    for job_id in sample:
        job = db.client.table("job_postings")\
            .select("id, title, title_classification")\
            .eq("id", job_id)\
            .execute()
        
        if job.data:
            j = job.data[0]
            print(f"  - {j.get('title_classification', 'NULL')}: {j.get('title', 'N/A')[:60]}")
        else:
            print(f"  - Job {job_id} NOT FOUND in job_postings (orphaned enrichment)")

# Find Data jobs WITHOUT any enrichment record
data_without_enrichment = all_data_ids - all_completed_ids
print(f"\nData jobs WITHOUT completed enrichment: {len(data_without_enrichment)}")

if data_without_enrichment:
    sample = list(data_without_enrichment)[:10]
    for job_id in sample:
        job = db.client.table("job_postings")\
            .select("id, title, is_active, posted_date_corrected")\
            .eq("id", job_id)\
            .execute()
        
        if job.data:
            j = job.data[0]
            active = "ACTIVE" if j.get("is_active") else "INACTIVE"
            posted = j.get("posted_date_corrected", "NULL")
            print(f"  - [{active}] {j.get('title', 'N/A')[:50]} - Posted: {posted}")
            
            # Check if enrichment record exists at all
            enrich = db.client.table("llm_enrichment")\
                .select("enrichment_completed_at, enrichment_error")\
                .eq("job_posting_id", job_id)\
                .execute()
            
            if enrich.data:
                e = enrich.data[0]
                print(f"      Has record: completed={e.get('enrichment_completed_at')}, error={e.get('enrichment_error')}")
            else:
                print(f"      NO enrichment record at all")

print("\n=== SUMMARY ===")
print(f"Total Data jobs: {all_data_jobs.count}")
print(f"Completed enrichments (no join): {completed_enrichments.count}")
print(f"Enriched via join (UI count): {enriched_via_join.count}")
print(f"Missing from join: {len(missing_from_join)}")
print(f"Never enriched: {len(data_without_enrichment)}")
print(f"\nExpected UI count: {all_data_jobs.count} total, {enriched_via_join.count} enriched")
print(f"Actual gap shown in UI: {all_data_jobs.count - enriched_via_join.count}")
