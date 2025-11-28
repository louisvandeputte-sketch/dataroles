#!/usr/bin/env python3
"""Check if GeoDynamics job is in job_ranking_view"""

from database.client import db

geodyn_id = "faf12622-68b4-477e-9ca2-59527485cdb1"

# Check in view
print("🔍 Checking job_ranking_view...")
result = db.client.table("job_ranking_view")\
    .select("id, title")\
    .eq("id", geodyn_id)\
    .execute()

if result.data:
    print(f"✅ Found in view: {result.data[0]['title']}")
else:
    print(f"❌ NOT in view!")
    
    # Check job_postings
    print(f"\n🔍 Checking job_postings...")
    jp_result = db.client.table("job_postings")\
        .select("id, title, is_active, company_id, location_id")\
        .eq("id", geodyn_id)\
        .single()\
        .execute()
    
    if jp_result.data:
        job = jp_result.data
        print(f"✅ Found in job_postings:")
        print(f"   - Title: {job['title']}")
        print(f"   - Active: {job['is_active']}")
        print(f"   - Company ID: {job['company_id']}")
        print(f"   - Location ID: {job['location_id']}")
        
        # Check if company exists
        if job['company_id']:
            comp_result = db.client.table("companies")\
                .select("id, name")\
                .eq("id", job['company_id'])\
                .execute()
            
            if comp_result.data:
                print(f"   - Company: {comp_result.data[0]['name']}")
            else:
                print(f"   - ⚠️ Company NOT FOUND (broken FK!)")
        
        # Check if location exists
        if job['location_id']:
            loc_result = db.client.table("locations")\
                .select("id, city")\
                .eq("id", job['location_id'])\
                .execute()
            
            if loc_result.data:
                print(f"   - Location: {loc_result.data[0]['city']}")
            else:
                print(f"   - ⚠️ Location NOT FOUND (broken FK!)")
