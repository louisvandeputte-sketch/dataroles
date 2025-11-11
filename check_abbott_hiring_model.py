#!/usr/bin/env python3
"""Check if Abbott has hiring_model field."""

from database.client import db

# Find Abbott
result = db.client.table("companies")\
    .select("id, name")\
    .ilike("name", "%Abbott%")\
    .limit(1)\
    .execute()

if result.data:
    company = result.data[0]
    company_id = company["id"]
    company_name = company["name"]
    
    print(f"Found: {company_name} (ID: {company_id})")
    print("=" * 80)
    
    # Check if hiring_model column exists
    print("\n1️⃣ Checking if hiring_model column exists...")
    try:
        master_data = db.client.table("company_master_data")\
            .select("hiring_model, hiring_model_en, hiring_model_nl, hiring_model_fr, ai_enriched_at")\
            .eq("company_id", company_id)\
            .single()\
            .execute()
        
        if master_data.data:
            data = master_data.data
            print("✅ Column exists!")
            print(f"\n   hiring_model:    {data.get('hiring_model')}")
            print(f"   hiring_model_en: {data.get('hiring_model_en')}")
            print(f"   hiring_model_nl: {data.get('hiring_model_nl')}")
            print(f"   hiring_model_fr: {data.get('hiring_model_fr')}")
            print(f"   Enriched at:     {data.get('ai_enriched_at')}")
            
            if data.get('hiring_model'):
                print(f"\n✅ Abbott has hiring_model: '{data.get('hiring_model')}'")
            else:
                print("\n⚠️ Abbott has NULL hiring_model (enriched with v14 or earlier)")
                print("   Re-enrich with v15 to populate this field")
        else:
            print("❌ No master data found for Abbott")
            
    except Exception as e:
        error_str = str(e)
        if "column" in error_str.lower() and "does not exist" in error_str.lower():
            print("❌ Column does NOT exist yet!")
            print("\n📋 Action needed:")
            print("   1. Run migration 026 in Supabase SQL Editor")
            print("   2. Copy SQL from: database/migrations/026_add_hiring_model.sql")
        else:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print("\n2️⃣ Checking UI display...")
    print("⚠️ UI needs to be updated to show hiring_model field")
    print("   Location: web/components/CompanyDetails.tsx (or similar)")
    print("   Add section similar to 'Company Size Classification'")
    
else:
    print("❌ Abbott not found in database")
