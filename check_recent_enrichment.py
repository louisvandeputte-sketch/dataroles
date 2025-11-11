#!/usr/bin/env python3
"""Check the most recently enriched company."""

from database.client import db
import json

# Get the most recently enriched company
result = db.client.table("company_master_data")\
    .select("company_id, ai_enriched_at, size_category, category_en, category_nl, category_fr, size_confidence, weetjes")\
    .not_.is_("ai_enriched_at", "null")\
    .order("ai_enriched_at", desc=True)\
    .limit(5)\
    .execute()

if result.data:
    print("Most recently enriched companies:")
    print("=" * 80)
    
    for i, enrichment in enumerate(result.data, 1):
        company_id = enrichment.get("company_id")
        
        # Get company name
        company = db.client.table("companies")\
            .select("name")\
            .eq("id", company_id)\
            .single()\
            .execute()
        
        company_name = company.data.get("name") if company.data else "Unknown"
        
        print(f"\n{i}. {company_name}")
        print(f"   Enriched: {enrichment.get('ai_enriched_at')}")
        print(f"   Size Category: {enrichment.get('size_category')}")
        print(f"   Category EN: {enrichment.get('category_en')}")
        print(f"   Category NL: {enrichment.get('category_nl')}")
        print(f"   Category FR: {enrichment.get('category_fr')}")
        print(f"   Confidence: {enrichment.get('size_confidence')}")
        
        weetjes = enrichment.get('weetjes')
        if weetjes:
            print(f"   Weetjes: {len(weetjes)} items")
        else:
            print(f"   Weetjes: None")
else:
    print("No enriched companies found")
