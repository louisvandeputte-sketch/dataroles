#!/usr/bin/env python3
"""Re-enrich Atlas Copco to test the fix."""

from database.client import db
from ingestion.company_enrichment import enrich_company

# Get Atlas Copco
result = db.client.table("companies")\
    .select("id, name, logo_url")\
    .ilike("name", "%Atlas Copco%")\
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
            .select("size_category, category_en, category_nl, category_fr, size_confidence, size_key_arguments, weetjes")\
            .eq("company_id", company_id)\
            .single()\
            .execute()
        
        if enrichment.data:
            data = enrichment.data
            print(f"\n📊 Saved Maturity Data:")
            print(f"  Size Category: {data.get('size_category')}")
            print(f"  Category EN: {data.get('category_en')}")
            print(f"  Category NL: {data.get('category_nl')}")
            print(f"  Category FR: {data.get('category_fr')}")
            print(f"  Confidence: {data.get('size_confidence')}")
            
            key_args = data.get('size_key_arguments')
            if key_args:
                print(f"\n  Key Arguments ({len(key_args)} items):")
                for i, arg in enumerate(key_args, 1):
                    print(f"    {i}. {arg[:80]}...")
            else:
                print(f"\n  Key Arguments: None")
            
            weetjes = data.get('weetjes')
            if weetjes:
                print(f"\n  Weetjes ({len(weetjes)} items):")
                for w in weetjes:
                    print(f"    - {w.get('category')}: {w.get('text_en', '')[:60]}...")
            else:
                print(f"\n  Weetjes: None")
    else:
        print(f"\n❌ Enrichment failed: {result.get('error')}")
else:
    print("Atlas Copco not found")
