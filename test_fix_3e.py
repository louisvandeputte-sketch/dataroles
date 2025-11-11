#!/usr/bin/env python3
"""Test the fix by re-enriching 3E company."""

from database.client import db
from ingestion.company_enrichment import enrich_company

# Get 3E company
result = db.client.table("companies")\
    .select("id, name, logo_url")\
    .ilike("name", "%3E%")\
    .limit(1)\
    .execute()

if result.data:
    company = result.data[0]
    company_id = company["id"]
    company_name = company["name"]
    company_url = company.get("logo_url")
    
    print(f"Re-enriching: {company_name} (ID: {company_id})")
    print("=" * 80)
    
    # Enrich the company
    result = enrich_company(company_id, company_name, company_url)
    
    if result["success"]:
        print("\n✅ Enrichment successful!")
        
        # Check the saved data
        enrichment = db.client.table("company_master_data")\
            .select("size_category, category_en, category_nl, category_fr, size_confidence, weetjes")\
            .eq("company_id", company_id)\
            .single()\
            .execute()
        
        if enrichment.data:
            data = enrichment.data
            print(f"\nSaved Data:")
            print(f"  Size Category: {data.get('size_category')}")
            print(f"  Category EN: {data.get('category_en')}")
            print(f"  Category NL: {data.get('category_nl')}")
            print(f"  Category FR: {data.get('category_fr')}")
            print(f"  Confidence: {data.get('size_confidence')}")
            
            weetjes = data.get('weetjes')
            if weetjes:
                print(f"  Weetjes: {len(weetjes)} items")
                for w in weetjes:
                    print(f"    - {w.get('category')}: {w.get('text_en', '')[:60]}...")
            else:
                print(f"  Weetjes: None")
    else:
        print(f"\n❌ Enrichment failed: {result.get('error')}")
else:
    print("Company '3E' not found")
