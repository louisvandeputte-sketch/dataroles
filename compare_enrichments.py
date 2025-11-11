#!/usr/bin/env python3
"""Compare enrichment output for ABAKUS vs 3E."""

from database.client import db
import json

companies = ["ABAKUS", "3E"]

for company_name in companies:
    result = db.client.table("companies")\
        .select("id, name")\
        .ilike("name", f"%{company_name}%")\
        .limit(1)\
        .execute()
    
    if result.data:
        company = result.data[0]
        company_id = company["id"]
        
        print(f"\n{'='*80}")
        print(f"Company: {company['name']} (ID: {company_id})")
        print('='*80)
        
        enrichment = db.client.table("company_master_data")\
            .select("ai_enriched_at, size_category, category_en, category_nl, category_fr, size_confidence, weetjes")\
            .eq("company_id", company_id)\
            .single()\
            .execute()
        
        if enrichment.data:
            data = enrichment.data
            print(f"Enriched: {data.get('ai_enriched_at')}")
            print(f"\nSize Category: {data.get('size_category')}")
            print(f"Category EN: {data.get('category_en')}")
            print(f"Category NL: {data.get('category_nl')}")
            print(f"Category FR: {data.get('category_fr')}")
            print(f"Confidence: {data.get('size_confidence')}")
            
            weetjes = data.get('weetjes')
            if weetjes:
                if isinstance(weetjes, str):
                    weetjes = json.loads(weetjes)
                print(f"\nWeetjes ({len(weetjes)} items):")
                for w in weetjes:
                    print(f"  - {w.get('category')}: {w.get('text_en', '')[:80]}...")
            else:
                print("\nWeetjes: None")
