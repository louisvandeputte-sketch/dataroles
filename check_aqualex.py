"""Check Aqualex company data."""

from database import db

# Find Aqualex - first find in companies table
companies_result = db.client.table("companies")\
    .select("id, name")\
    .ilike("name", "%aqualex%")\
    .execute()

if not companies_result.data:
    print("Aqualex not found in companies table")
    exit(1)

company_id = companies_result.data[0]['id']
print(f"Found company: {companies_result.data[0]['name']} (ID: {company_id})")

# Now get from company_master_data
result = db.client.table("company_master_data")\
    .select("*")\
    .eq("company_id", company_id)\
    .execute()

if result.data:
    company = result.data[0]
    print("="*80)
    print(f"Company Master Data for: {companies_result.data[0]['name']}")
    print("="*80)
    print(f"\nID: {company['id']}")
    print(f"company_id: {company.get('company_id')}")
    print(f"ai_enriched: {company.get('ai_enriched')}")
    print(f"ai_enriched_at: {company.get('ai_enriched_at')}")
    print(f"\nSize fields:")
    print(f"  size_category: {company.get('size_category')}")
    print(f"  size_confidence: {company.get('size_confidence')}")
    print(f"  size_enriched_at: {company.get('size_enriched_at')}")
    print(f"  size_key_arguments: {company.get('size_key_arguments')}")
    print(f"  size_sources: {company.get('size_sources')}")
    
    print(f"\nOther enrichment fields:")
    print(f"  sector_en: {company.get('sector_en')}")
    print(f"  locatie_belgie: {company.get('locatie_belgie')}")
    print(f"  aantal_werknemers: {company.get('aantal_werknemers')}")
else:
    print("Aqualex not found in company_master_data")
