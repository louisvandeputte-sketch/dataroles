#!/usr/bin/env python3
"""Test company enrichment v15 with hiring_model field."""

from ingestion.company_enrichment import enrich_company
from database.client import db
import json

print("🧪 Testing Company Enrichment v15 - Hiring Model")
print("=" * 80)

# Test companies (recruitment vs direct)
test_companies = [
    {
        "name": "Randstad",
        "expected_model": "recruitment",
        "reason": "Staffing/recruitment company"
    },
    {
        "name": "Atlas Copco Group",
        "expected_model": "direct",
        "reason": "Manufacturing company, hires for itself"
    }
]

for test in test_companies:
    company_name = test["name"]
    expected = test["expected_model"]
    
    print(f"\n{'=' * 80}")
    print(f"Testing: {company_name}")
    print(f"Expected hiring_model: {expected}")
    print(f"Reason: {test['reason']}")
    print("-" * 80)
    
    # Find company in database
    result = db.client.table("companies")\
        .select("id, name")\
        .ilike("name", f"%{company_name}%")\
        .limit(1)\
        .execute()
    
    if not result.data:
        print(f"❌ Company not found in database: {company_name}")
        continue
    
    company = result.data[0]
    company_id = company["id"]
    
    print(f"Found company ID: {company_id}")
    
    # Enrich company
    print(f"\n🔄 Enriching with prompt v15...")
    enrichment_result = enrich_company(company_id, company_name)
    
    if enrichment_result.get("success"):
        print("✅ Enrichment successful")
        
        # Check database for hiring_model
        master_data = db.client.table("company_master_data")\
            .select("hiring_model, hiring_model_en, hiring_model_nl, hiring_model_fr")\
            .eq("company_id", company_id)\
            .single()\
            .execute()
        
        if master_data.data:
            data = master_data.data
            hiring_model = data.get("hiring_model")
            
            print(f"\n📊 Hiring Model Results:")
            print(f"   Canonical: {hiring_model}")
            print(f"   English:   {data.get('hiring_model_en')}")
            print(f"   Dutch:     {data.get('hiring_model_nl')}")
            print(f"   French:    {data.get('hiring_model_fr')}")
            
            if hiring_model == expected:
                print(f"\n✅ CORRECT: hiring_model = '{hiring_model}' (expected '{expected}')")
            else:
                print(f"\n⚠️ UNEXPECTED: hiring_model = '{hiring_model}' (expected '{expected}')")
        else:
            print("❌ No master data found")
    else:
        error = enrichment_result.get("error", "Unknown error")
        print(f"❌ Enrichment failed: {error}")

print("\n" + "=" * 80)
print("\n📋 Summary:")
print("   - Prompt v15 adds hiring_model field")
print("   - Values: 'recruitment', 'direct', 'unknown'")
print("   - Multilingual: _en, _nl, _fr variants")
print("\n✅ Test complete!")
