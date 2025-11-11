#!/usr/bin/env python3
"""Debug Atlas Copco enrichment."""

from database.client import db
import json

# Get Atlas Copco
result = db.client.table("companies")\
    .select("id, name")\
    .ilike("name", "%Atlas Copco%")\
    .limit(1)\
    .execute()

if result.data:
    company = result.data[0]
    company_id = company["id"]
    company_name = company["name"]
    
    print(f"Company: {company_name} (ID: {company_id})")
    print("=" * 80)
    
    # Get ALL enrichment data
    enrichment = db.client.table("company_master_data")\
        .select("*")\
        .eq("company_id", company_id)\
        .single()\
        .execute()
    
    if enrichment.data:
        data = enrichment.data
        
        print(f"\n📅 Enrichment Date: {data.get('ai_enriched_at')}")
        print(f"✅ AI Enriched: {data.get('ai_enriched')}")
        print(f"❌ Error: {data.get('ai_enrichment_error')}")
        
        print(f"\n🌐 Basic Info:")
        print(f"  - Website: {data.get('bedrijfswebsite')}")
        print(f"  - Jobs Page: {data.get('jobspagina')}")
        print(f"  - HR Email: {data.get('email_hr')}")
        print(f"  - General Email: {data.get('email_algemeen')}")
        
        print(f"\n🏢 Sector:")
        print(f"  - EN: {data.get('sector_en')}")
        print(f"  - NL: {data.get('sector_nl')}")
        print(f"  - FR: {data.get('sector_fr')}")
        
        print(f"\n👥 Employees: {data.get('aantal_werknemers')}")
        
        print(f"\n📊 Size Classification:")
        print(f"  - size_category: {data.get('size_category')}")
        print(f"  - category_en: {data.get('category_en')}")
        print(f"  - category_nl: {data.get('category_nl')}")
        print(f"  - category_fr: {data.get('category_fr')}")
        print(f"  - size_confidence: {data.get('size_confidence')}")
        print(f"  - size_enriched_at: {data.get('size_enriched_at')}")
        print(f"  - size_enrichment_error: {data.get('size_enrichment_error')}")
        
        print(f"\n🔑 Key Arguments:")
        key_args = data.get('size_key_arguments')
        if key_args:
            if isinstance(key_args, str):
                key_args = json.loads(key_args)
            for arg in key_args:
                print(f"  - {arg}")
        else:
            print(f"  None")
        
        print(f"\n🔗 Sources:")
        sources = data.get('size_sources')
        if sources:
            if isinstance(sources, str):
                sources = json.loads(sources)
            for src in sources:
                print(f"  - {src}")
        else:
            print(f"  None")
        
        print(f"\n💡 Weetjes:")
        weetjes = data.get('weetjes')
        if weetjes:
            if isinstance(weetjes, str):
                weetjes = json.loads(weetjes)
            print(f"  Count: {len(weetjes)}")
            for w in weetjes:
                print(f"  - {w.get('category')}: {w.get('text_en', '')[:60]}...")
        else:
            print(f"  None")
    else:
        print("No enrichment data found")
else:
    print("Atlas Copco not found")
