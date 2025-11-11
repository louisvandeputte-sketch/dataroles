#!/usr/bin/env python3
"""Check the 10 most recently attempted company enrichments."""

from database.client import db
import json

# Get the 10 most recently enriched companies (success or fail)
result = db.client.table("company_master_data")\
    .select("company_id, ai_enriched, ai_enriched_at, ai_enrichment_error, bedrijfswebsite, sector_en, size_category")\
    .order("ai_enriched_at", desc=True)\
    .limit(10)\
    .execute()

if result.data:
    print("📊 10 Most Recently Enriched Companies:")
    print("=" * 80)
    
    success_count = 0
    failed_count = 0
    
    for i, enrichment in enumerate(result.data, 1):
        company_id = enrichment.get("company_id")
        ai_enriched = enrichment.get("ai_enriched")
        error = enrichment.get("ai_enrichment_error")
        enriched_at = enrichment.get("ai_enriched_at")
        website = enrichment.get("bedrijfswebsite")
        sector = enrichment.get("sector_en")
        size = enrichment.get("size_category")
        
        # Get company name
        company = db.client.table("companies")\
            .select("name")\
            .eq("id", company_id)\
            .single()\
            .execute()
        
        company_name = company.data.get("name") if company.data else "Unknown"
        
        if error:
            status = "❌ FAILED"
            failed_count += 1
        elif ai_enriched:
            status = "✅ SUCCESS"
            success_count += 1
        else:
            status = "⚠️ UNKNOWN"
        
        print(f"\n{i}. {status} - {company_name}")
        print(f"   Enriched at: {enriched_at}")
        
        if error:
            print(f"   Error: {error[:150]}...")
        else:
            print(f"   Website: {website or 'N/A'}")
            print(f"   Sector: {sector or 'N/A'}")
            print(f"   Size: {size or 'N/A'}")
    
    print("\n" + "=" * 80)
    print(f"Summary: {success_count} successful, {failed_count} failed")
else:
    print("No enrichments found")
