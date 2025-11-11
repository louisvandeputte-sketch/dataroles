#!/usr/bin/env python3
"""Check if Accountable has hiring_model field."""

from database.client import db

# Find Accountable
result = db.client.table("companies")\
    .select("id, name")\
    .ilike("name", "%Accountable%")\
    .limit(5)\
    .execute()

if result.data:
    for company in result.data:
        company_id = company["id"]
        company_name = company["name"]
        
        print(f"\n{'=' * 80}")
        print(f"Company: {company_name} (ID: {company_id})")
        print("=" * 80)
        
        # Check master data
        try:
            master_data = db.client.table("company_master_data")\
                .select("hiring_model, hiring_model_en, hiring_model_nl, hiring_model_fr, ai_enriched_at")\
                .eq("company_id", company_id)\
                .single()\
                .execute()
            
            if master_data.data:
                data = master_data.data
                print(f"\n✅ Master data found:")
                print(f"   hiring_model:    {data.get('hiring_model')}")
                print(f"   hiring_model_en: {data.get('hiring_model_en')}")
                print(f"   hiring_model_nl: {data.get('hiring_model_nl')}")
                print(f"   hiring_model_fr: {data.get('hiring_model_fr')}")
                print(f"   Enriched at:     {data.get('ai_enriched_at')}")
                
                if data.get('hiring_model'):
                    print(f"\n✅ Has hiring_model: '{data.get('hiring_model')}'")
                else:
                    print(f"\n⚠️ hiring_model is NULL")
                    print(f"   Enriched at: {data.get('ai_enriched_at')}")
                    
                    # Check when it was enriched
                    from datetime import datetime
                    if data.get('ai_enriched_at'):
                        enriched_time = datetime.fromisoformat(data.get('ai_enriched_at').replace('Z', '+00:00'))
                        print(f"   Time: {enriched_time}")
                        
                        # Check if it's recent (after v15 was deployed)
                        v15_deploy_time = datetime(2025, 11, 9, 22, 0, 0)  # Approx when v15 was deployed
                        if enriched_time > v15_deploy_time:
                            print(f"\n❌ PROBLEM: Enriched AFTER v15 deployment but hiring_model is NULL!")
                            print(f"   This suggests the prompt v15 is not working correctly")
                        else:
                            print(f"\n✅ Enriched BEFORE v15 deployment (v14 or earlier)")
                            print(f"   Re-enrich to get hiring_model")
            else:
                print("❌ No master data found")
                
        except Exception as e:
            print(f"❌ Error: {e}")
else:
    print("❌ Accountable not found in database")

print("\n" + "=" * 80)
print("\n📋 Analysis:")
print("   If enriched at 23:38:08 (after v15 deployment ~23:00)")
print("   but hiring_model is NULL, then:")
print("   1. Prompt v15 is not being used")
print("   2. OR prompt v15 is not returning hiring_model")
print("   3. OR save logic is not storing hiring_model")
