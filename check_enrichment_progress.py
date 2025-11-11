#!/usr/bin/env python3
"""Check current enrichment progress."""

from database.client import db

print("Company Enrichment Progress")
print("=" * 80)

# Total companies
total = db.client.table("companies")\
    .select("id", count="exact")\
    .execute()

print(f"\n📊 Total companies: {total.count}")

# Enriched companies (have master data)
enriched = db.client.table("company_master_data")\
    .select("company_id, bedrijfswebsite, jobspagina", count="exact")\
    .execute()

print(f"✅ Enriched companies: {enriched.count}")
print(f"⏳ Not enriched: {total.count - enriched.count}")
print(f"📈 Progress: {enriched.count / total.count * 100:.1f}%")

# Show last 5 enriched with company names
if enriched.data:
    print(f"\n🔍 Last 5 enriched companies:")
    for master_data in enriched.data[-5:]:
        # Get company name
        company = db.client.table("companies")\
            .select("name")\
            .eq("id", master_data['company_id'])\
            .single()\
            .execute()
        
        website = master_data.get('bedrijfswebsite', 'N/A')
        jobs_page = master_data.get('jobspagina', 'N/A')
        
        if website and len(website) > 50:
            website = website[:50] + "..."
        if jobs_page and len(jobs_page) > 50:
            jobs_page = jobs_page[:50] + "..."
            
        print(f"  • {company.data['name'][:40]}")
        print(f"    Website: {website or 'N/A'}")
        print(f"    Jobs: {jobs_page or 'N/A'}")

print("\n" + "=" * 80)
print("\n💡 To stop current enrichment: Restart the web server (Ctrl+C)")
print("   All enriched data is already saved in the database!")
