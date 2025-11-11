#!/usr/bin/env python3
"""Debug script to check enrichment output for 3E company."""

from database.client import db
import json

# Get 3E company data
result = db.client.table("companies")\
    .select("id, name")\
    .ilike("name", "%3E%")\
    .limit(1)\
    .execute()

if result.data:
    company = result.data[0]
    company_id = company["id"]
    company_name = company["name"]
    
    print(f"Company: {company_name} (ID: {company_id})")
    print("=" * 80)
    
    # Get enrichment data
    enrichment = db.client.table("company_master_data")\
        .select("*")\
        .eq("company_id", company_id)\
        .single()\
        .execute()
    
    if enrichment.data:
        data = enrichment.data
        
        print("\n📅 Enrichment Date:", data.get("ai_enriched_at"))
        print("\n🌐 Basic Info:")
        print(f"  - Website: {data.get('bedrijfswebsite')}")
        print(f"  - Jobs Page: {data.get('jobspagina')}")
        print(f"  - HR Email: {data.get('email_hr')}")
        print(f"  - General Email: {data.get('email_algemeen')}")
        
        print("\n🏢 Sector:")
        print(f"  - EN: {data.get('sector_en')}")
        print(f"  - NL: {data.get('sector_nl')}")
        print(f"  - FR: {data.get('sector_fr')}")
        
        print(f"\n👥 Employees: {data.get('aantal_werknemers')}")
        
        print("\n📊 Size Classification:")
        print(f"  - Category (size_category): {data.get('size_category')}")
        print(f"  - Category EN: {data.get('category_en')}")
        print(f"  - Category NL: {data.get('category_nl')}")
        print(f"  - Category FR: {data.get('category_fr')}")
        print(f"  - Confidence: {data.get('size_confidence')}")
        print(f"  - Key Arguments: {data.get('size_key_arguments')}")
        print(f"  - Sources: {data.get('size_sources')}")
        
        print("\n💡 Weetjes (Factlets):")
        weetjes = data.get('weetjes')
        if weetjes:
            if isinstance(weetjes, str):
                weetjes = json.loads(weetjes)
            print(json.dumps(weetjes, indent=2, ensure_ascii=False))
        else:
            print("  None")
        
        print("\n📝 Descriptions:")
        print(f"  - NL: {data.get('bedrijfsomschrijving_nl')[:100] if data.get('bedrijfsomschrijving_nl') else 'None'}...")
        print(f"  - FR: {data.get('bedrijfsomschrijving_fr')[:100] if data.get('bedrijfsomschrijving_fr') else 'None'}...")
        print(f"  - EN: {data.get('bedrijfsomschrijving_en')[:100] if data.get('bedrijfsomschrijving_en') else 'None'}...")
    else:
        print("No enrichment data found")
else:
    print("Company '3E' not found")
