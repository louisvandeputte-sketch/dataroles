#!/usr/bin/env python3
"""Find jobs that failed enrichment or were never enriched."""

from database.client import db
import json

print("🔍 Analyzing Job Enrichment Status")
print("=" * 80)

# 1. Jobs with enrichment errors
print("\n❌ Jobs with Enrichment Errors:")
print("-" * 80)

error_result = db.client.table("llm_enrichment")\
    .select("job_posting_id, enrichment_error, enrichment_completed_at")\
    .not_.is_("enrichment_error", "null")\
    .order("enrichment_completed_at", desc=True)\
    .limit(20)\
    .execute()

if error_result.data:
    for i, enrichment in enumerate(error_result.data, 1):
        job_id = enrichment.get("job_posting_id")
        error = enrichment.get("enrichment_error")
        completed_at = enrichment.get("enrichment_completed_at")
        
        # Get job title
        job = db.client.table("job_postings")\
            .select("title, company_name")\
            .eq("id", job_id)\
            .single()\
            .execute()
        
        if job.data:
            print(f"\n{i}. {job.data.get('title')}")
            print(f"   Company: {job.data.get('company_name')}")
            print(f"   Failed at: {completed_at}")
            print(f"   Error: {error[:150]}...")
else:
    print("✅ No jobs with enrichment errors found")

# 2. Jobs that were never enriched (no llm_enrichment record or enrichment_completed_at is NULL)
print("\n\n⏳ Jobs Never Enriched (with title_classification = 'Data'):")
print("-" * 80)

# Get jobs with Data classification but no enrichment
unenriched_result = db.client.table("job_postings")\
    .select("id, title, company_name, posted_at")\
    .eq("title_classification", "Data")\
    .order("posted_at", desc=True)\
    .limit(100)\
    .execute()

if unenriched_result.data:
    never_enriched = []
    
    for job in unenriched_result.data:
        job_id = job.get("id")
        
        # Check if enrichment exists
        enrichment = db.client.table("llm_enrichment")\
            .select("enrichment_completed_at")\
            .eq("job_posting_id", job_id)\
            .execute()
        
        if not enrichment.data or not enrichment.data[0].get("enrichment_completed_at"):
            never_enriched.append(job)
    
    if never_enriched:
        print(f"\nFound {len(never_enriched)} jobs that were never enriched:")
        for i, job in enumerate(never_enriched[:10], 1):
            print(f"\n{i}. {job.get('title')}")
            print(f"   Company: {job.get('company_name')}")
            print(f"   Posted: {job.get('posted_at')}")
            print(f"   Job ID: {job.get('id')}")
        
        if len(never_enriched) > 10:
            print(f"\n... and {len(never_enriched) - 10} more")
    else:
        print("✅ All Data jobs have been enriched")
else:
    print("No Data jobs found")

print("\n" + "=" * 80)
print("\n💡 To fix failed enrichments:")
print("   1. Run the database migration: 025_add_llm_enrichment_error.sql")
print("   2. Re-enrich failed jobs via API: POST /api/jobs/{job_id}/enrich?force=true")
print("   3. Or use batch enrichment: POST /api/jobs/enrich/batch")
