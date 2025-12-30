#!/usr/bin/env python3
"""Investigate why jobs are marked as 'already enriched' when they shouldn't be."""

from database.client import db

print("=== FALSE 'ALREADY ENRICHED' INVESTIGATION ===\n")

# Check the "Customer Journey Expert - GenAI Chatbot" job that was skipped
job_id = "27f7e4b3-0aa2-4df8-849a-b29224ec6267"

print(f"Checking job: {job_id}")

# Get job details
job = db.client.table("job_postings")\
    .select("id, title, title_classification")\
    .eq("id", job_id)\
    .single()\
    .execute()

print(f"Job: {job.data.get('title')}")
print(f"Classification: {job.data.get('title_classification')}")

# Get enrichment record
enrichment = db.client.table("llm_enrichment")\
    .select("*")\
    .eq("job_posting_id", job_id)\
    .maybe_single()\
    .execute()

if enrichment.data:
    e = enrichment.data
    print(f"\n=== ENRICHMENT RECORD ===")
    print(f"ID: {e.get('id')}")
    print(f"enrichment_completed_at: {e.get('enrichment_completed_at')}")
    print(f"enrichment_error: {e.get('enrichment_error')}")
    print(f"type_datarol: {e.get('type_datarol')}")
    print(f"skills_must_have: {e.get('skills_must_have')}")
    print(f"skills_nice_to_have: {e.get('skills_nice_to_have')}")
    print(f"created_at: {e.get('created_at')}")
    
    # Check if this is truly enriched
    has_completed = e.get('enrichment_completed_at') is not None
    has_type = e.get('type_datarol') is not None
    has_skills = e.get('skills_must_have') is not None
    
    print(f"\n=== ENRICHMENT STATUS ===")
    print(f"Has completed_at: {has_completed}")
    print(f"Has type_datarol: {has_type}")
    print(f"Has skills: {has_skills}")
    
    if has_completed and not has_type:
        print("\n🚨 PROBLEM FOUND:")
        print("Job has enrichment_completed_at but NO type_datarol!")
        print("This means enrichment was marked complete but failed to extract data.")
        print("The job should be re-enriched, but the check only looks at completed_at.")
else:
    print("\n❌ No enrichment record found!")

# Check the enrichment check logic
print(f"\n=== ENRICHMENT CHECK LOGIC ===")
print("The service checks:")
print("1. Get all enriched IDs: WHERE enrichment_completed_at IS NOT NULL")
print("2. Skip if job_id in enriched_ids")
print("\nPROBLEM: This doesn't check if enrichment actually succeeded!")
print("Jobs with completed_at but NULL type_datarol are skipped incorrectly.")

# Count how many jobs have this issue
print(f"\n=== COUNTING INCOMPLETE ENRICHMENTS ===")
incomplete = db.client.table("llm_enrichment")\
    .select("job_posting_id, job_postings!inner(title_classification)", count="exact")\
    .eq("job_postings.title_classification", "Data")\
    .not_.is_("enrichment_completed_at", "null")\
    .is_("type_datarol", "null")\
    .execute()

print(f"Jobs with completed_at but NULL type_datarol: {incomplete.count}")

if incomplete.data:
    print(f"\nSample of {min(10, len(incomplete.data))} incomplete enrichments:")
    for i, e in enumerate(incomplete.data[:10], 1):
        job_id = e.get("job_posting_id")
        # Get job title
        job = db.client.table("job_postings")\
            .select("title")\
            .eq("id", job_id)\
            .maybe_single()\
            .execute()
        
        title = job.data.get("title", "N/A") if job.data else "N/A"
        print(f"{i}. {title[:60]}")

print(f"\n=== ROOT CAUSE ===")
print("The enrichment check in auto_enrich_service.py is too simple:")
print("  enriched_ids = {e['job_posting_id'] for e in enriched.data}")
print("  if job['id'] not in enriched_ids: ...")
print("\nIt should check:")
print("  1. enrichment_completed_at IS NOT NULL")
print("  2. AND type_datarol IS NOT NULL (or other success indicators)")
print("\nThis explains why OpenAI API is not called - jobs are incorrectly skipped!")
