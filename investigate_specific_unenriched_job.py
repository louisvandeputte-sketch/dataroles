#!/usr/bin/env python3
"""Investigate why 'HR Strategy, Workforce & People Analytics Director' is not being enriched."""

from database.client import db

print("=== INVESTIGATING SPECIFIC UNENRICHED JOB ===\n")

# Search for the job
title = "HR Strategy, Workforce & People Analytics Director"
company = "bpost"

print(f"Searching for: {title}")
print(f"Company: {company}\n")

# Find job
jobs = db.client.table("job_postings")\
    .select("*")\
    .ilike("title", f"%{title}%")\
    .execute()

if not jobs.data:
    print("Job not found by title, trying partial match...")
    jobs = db.client.table("job_postings")\
        .select("*")\
        .ilike("title", "%HR Strategy%")\
        .execute()

if jobs.data:
    job = jobs.data[0]
    print(f"=== JOB FOUND ===")
    print(f"ID: {job['id']}")
    print(f"Title: {job['title']}")
    print(f"Company ID: {job['company_id']}")
    print(f"Title Classification: {job.get('title_classification')}")
    print(f"Is Active: {job.get('is_active')}")
    print(f"Posted Date: {job.get('posted_date')}")
    print(f"Posted Date Corrected: {job.get('posted_date_corrected')}")
    print(f"LinkedIn Job ID: {job.get('linkedin_job_id')}")
    
    # Check enrichment record
    print(f"\n=== ENRICHMENT RECORD ===")
    enrichment = db.client.table("llm_enrichment")\
        .select("*")\
        .eq("job_posting_id", job['id'])\
        .maybe_single()\
        .execute()
    
    if enrichment.data:
        e = enrichment.data
        print(f"Enrichment ID: {e.get('id')}")
        print(f"Created At: {e.get('created_at')}")
        print(f"Completed At: {e.get('enrichment_completed_at')}")
        print(f"Error: {e.get('enrichment_error')}")
        print(f"Type Datarol: {e.get('type_datarol')}")
        print(f"Skills Must Have: {e.get('skills_must_have')}")
    else:
        print("❌ NO ENRICHMENT RECORD EXISTS")
    
    # Check if job would be picked up by service
    print(f"\n=== WOULD SERVICE PICK THIS UP? ===")
    
    # Check 1: Title classification
    if job.get('title_classification') != 'Data':
        print(f"❌ FAIL: title_classification = '{job.get('title_classification')}' (not 'Data')")
        print("   Service only processes jobs with title_classification='Data'")
    else:
        print(f"✅ PASS: title_classification = 'Data'")
    
    # Check 2: Is active
    if not job.get('is_active'):
        print(f"❌ FAIL: is_active = False")
        print("   Service only processes active jobs")
    else:
        print(f"✅ PASS: is_active = True")
    
    # Check 3: Would it be in first 500 by posted_date?
    print(f"\n=== CHECKING QUERY POSITION ===")
    
    # Simulate service query
    all_data_jobs = db.client.table("job_postings")\
        .select("id, title, posted_date")\
        .eq("title_classification", "Data")\
        .eq("is_active", True)\
        .order("posted_date", desc=True)\
        .limit(500)\
        .execute()
    
    job_ids_in_query = [j['id'] for j in all_data_jobs.data]
    
    if job['id'] in job_ids_in_query:
        position = job_ids_in_query.index(job['id']) + 1
        print(f"✅ PASS: Job is at position {position} in service query (top 500)")
    else:
        print(f"❌ FAIL: Job is NOT in first 500 jobs sorted by posted_date DESC")
        print(f"   Posted date: {job.get('posted_date')}")
        print(f"   This job is too old to be picked up by current query")
    
    # Check 4: Is it in enriched_ids set?
    print(f"\n=== CHECKING ENRICHED IDS SET ===")
    
    enriched = db.client.table("llm_enrichment")\
        .select("job_posting_id")\
        .not_.is_("enrichment_completed_at", "null")\
        .limit(3000)\
        .execute()
    
    enriched_ids = {e["job_posting_id"] for e in enriched.data}
    
    if job['id'] in enriched_ids:
        print(f"❌ FAIL: Job IS in enriched_ids (would be skipped)")
        print(f"   Service thinks this job is already enriched")
    else:
        print(f"✅ PASS: Job is NOT in enriched_ids (would be processed)")
    
    print(f"\n=== DIAGNOSIS ===")
    
    if job.get('title_classification') != 'Data':
        print("🔍 ROOT CAUSE: Job is not classified as 'Data'")
        print("   Solution: Job needs title classification first")
    elif not job.get('is_active'):
        print("🔍 ROOT CAUSE: Job is inactive")
    elif job['id'] not in job_ids_in_query:
        print("🔍 ROOT CAUSE: Job is not in first 500 by posted_date")
        print("   The service query limit (500) is too small")
        print("   OR job is too old (posted_date is NULL or very old)")
    elif job['id'] in enriched_ids:
        print("🔍 ROOT CAUSE: Job is incorrectly marked as enriched")
        print("   Check enrichment record for incomplete data")
    else:
        print("✅ Job SHOULD be picked up by service!")
        print("   Check service logs for why it's being skipped")

else:
    print("❌ Job not found in database")
    print("\nTrying to find by LinkedIn Job ID...")
    
    linkedin_id = "4338491028"
    job = db.client.table("job_postings")\
        .select("*")\
        .eq("linkedin_job_id", linkedin_id)\
        .maybe_single()\
        .execute()
    
    if job.data:
        print(f"Found by LinkedIn ID: {job.data['title']}")
    else:
        print("Job not found by LinkedIn ID either")
