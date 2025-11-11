#!/usr/bin/env python3
"""Check recently failed enrichments."""

from database.client import db
import json

# Get recently failed enrichments (last 10)
result = db.client.table("company_master_data")\
    .select("company_id, ai_enrichment_error, ai_enriched_at")\
    .not_.is_("ai_enrichment_error", "null")\
    .order("ai_enriched_at", desc=True)\
    .limit(10)\
    .execute()

if result.data:
    print("❌ Recently Failed Company Enrichments:")
    print("=" * 80)
    
    for i, enrichment in enumerate(result.data, 1):
        company_id = enrichment.get("company_id")
        error = enrichment.get("ai_enrichment_error")
        enriched_at = enrichment.get("ai_enriched_at")
        
        # Get company name
        company = db.client.table("companies")\
            .select("name")\
            .eq("id", company_id)\
            .single()\
            .execute()
        
        company_name = company.data.get("name") if company.data else "Unknown"
        
        print(f"\n{i}. {company_name}")
        print(f"   Company ID: {company_id}")
        print(f"   Failed at: {enriched_at}")
        print(f"   Error: {error[:200]}...")
else:
    print("✅ No failed enrichments found")

print("\n" + "=" * 80)

# Also check for jobs that failed title classification
print("\n❌ Recently Failed Job Title Classifications:")
print("=" * 80)

job_result = db.client.table("job_postings")\
    .select("id, title, title_classification_error, title_classification_at")\
    .not_.is_("title_classification_error", "null")\
    .order("title_classification_at", desc=True)\
    .limit(10)\
    .execute()

if job_result.data:
    for i, job in enumerate(job_result.data, 1):
        print(f"\n{i}. {job.get('title')}")
        print(f"   Job ID: {job.get('id')}")
        print(f"   Failed at: {job.get('title_classification_at')}")
        print(f"   Error: {job.get('title_classification_error')[:200]}...")
else:
    print("✅ No failed job classifications found")
