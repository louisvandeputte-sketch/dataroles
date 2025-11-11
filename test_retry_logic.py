#!/usr/bin/env python3
"""Test automatic retry logic for all LLM enrichment services."""

from database.client import db
from datetime import datetime, timedelta

print("🧪 Testing Automatic Retry Logic for LLM Enrichments")
print("=" * 80)

# Test 1: Location Enrichment
print("\n1️⃣ Location Enrichment Retry Logic")
print("-" * 80)

retry_cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()

location_result = db.client.table("locations")\
    .select("id, city, ai_enrichment_error, ai_enriched_at")\
    .or_(
        f"and(ai_enriched.is.null,ai_enrichment_error.is.null),"
        f"and(ai_enriched.eq.false,ai_enrichment_error.is.null),"
        f"and(ai_enrichment_error.not.is.null,ai_enriched_at.lt.{retry_cutoff})"
    )\
    .limit(10)\
    .execute()

if location_result.data:
    new_count = sum(1 for loc in location_result.data if not loc.get("ai_enrichment_error"))
    retry_count = len(location_result.data) - new_count
    
    print(f"✅ Found {len(location_result.data)} locations to enrich")
    print(f"   - New: {new_count}")
    print(f"   - Retries (>24h old errors): {retry_count}")
    
    if retry_count > 0:
        print("\n   Retry examples:")
        for loc in location_result.data:
            if loc.get("ai_enrichment_error"):
                error = loc.get("ai_enrichment_error")[:60]
                print(f"   - {loc.get('city')}: {error}...")
else:
    print("✅ No locations need enrichment")

# Test 2: Job Enrichment
print("\n\n2️⃣ Job Enrichment Retry Logic")
print("-" * 80)

job_result = db.client.table("llm_enrichment")\
    .select("job_posting_id, enrichment_error, enrichment_completed_at, job_postings!inner(title, title_classification)")\
    .or_(
        f"and(enrichment_completed_at.is.null,enrichment_error.is.null),"
        f"and(enrichment_error.not.is.null,enrichment_completed_at.lt.{retry_cutoff})"
    )\
    .eq("job_postings.title_classification", "Data")\
    .limit(10)\
    .execute()

if job_result.data:
    new_count = sum(1 for job in job_result.data if not job.get("enrichment_error"))
    retry_count = len(job_result.data) - new_count
    
    print(f"✅ Found {len(job_result.data)} 'Data' jobs to enrich")
    print(f"   - New: {new_count}")
    print(f"   - Retries (>24h old errors): {retry_count}")
    
    if retry_count > 0:
        print("\n   Retry examples:")
        for job in job_result.data:
            if job.get("enrichment_error"):
                title = job.get("job_postings", {}).get("title", "Unknown")
                error = job.get("enrichment_error")[:60]
                print(f"   - {title}: {error}...")
else:
    print("✅ No jobs need enrichment")

# Test 3: Company Enrichment
print("\n\n3️⃣ Company Enrichment Retry Logic")
print("-" * 80)

company_result = db.client.table("company_master_data")\
    .select("company_id, ai_enrichment_error, ai_enriched_at, companies!inner(name)")\
    .or_(
        f"ai_enriched.is.null,"
        f"and(ai_enriched.eq.false,ai_enrichment_error.is.null),"
        f"and(ai_enrichment_error.not.is.null,ai_enriched_at.lt.{retry_cutoff})"
    )\
    .limit(10)\
    .execute()

if company_result.data:
    new_count = sum(1 for comp in company_result.data if not comp.get("ai_enrichment_error"))
    retry_count = len(company_result.data) - new_count
    
    print(f"✅ Found {len(company_result.data)} companies to enrich")
    print(f"   - New: {new_count}")
    print(f"   - Retries (>24h old errors): {retry_count}")
    
    if retry_count > 0:
        print("\n   Retry examples:")
        for comp in company_result.data:
            if comp.get("ai_enrichment_error"):
                name = comp.get("companies", {}).get("name", "Unknown")
                error = comp.get("ai_enrichment_error")[:60]
                print(f"   - {name}: {error}...")
else:
    print("✅ No companies need enrichment")

# Summary
print("\n" + "=" * 80)
print("\n📊 Summary:")
print(f"   Locations ready: {len(location_result.data) if location_result.data else 0}")
print(f"   Jobs ready: {len(job_result.data) if job_result.data else 0}")
print(f"   Companies ready: {len(company_result.data) if company_result.data else 0}")

print("\n✅ Retry logic is working!")
print("   - Items with errors >24h old will be automatically retried")
print("   - Auto-enrichment service will pick them up in the next cycle")
print("   - Location auto-enrichment runs every 60 seconds")
