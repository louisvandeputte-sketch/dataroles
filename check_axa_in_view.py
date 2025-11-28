#!/usr/bin/env python3
"""Check if AXA job is in job_ranking_view"""

from database.client import db

# Find AXA job in view
result = db.client.table("job_ranking_view")\
    .select("id, title, company_name, posted_date, posted_date_corrected, is_active")\
    .ilike("title", "%AI Analyst%")\
    .ilike("company_name", "%AXA%")\
    .execute()

print(f"\n🔍 AXA AI Analyst in job_ranking_view:")
if result.data:
    for job in result.data:
        print(f"   ID: {job['id']}")
        print(f"   Title: {job['title']}")
        print(f"   Company: {job['company_name']}")
        print(f"   Posted: {job['posted_date']}")
        print(f"   Corrected: {job['posted_date_corrected']}")
        print(f"   Active: {job['is_active']}")
else:
    print("   ❌ NOT FOUND in view!")
    
    # Check if it's in job_postings
    jp_result = db.client.table("job_postings")\
        .select("id, title, is_active, title_classification")\
        .ilike("title", "%AI Analyst%")\
        .execute()
    
    print(f"\n🔍 AXA AI Analyst in job_postings:")
    for job in jp_result.data:
        if 'AXA' in str(job):
            print(f"   ID: {job['id']}")
            print(f"   Title: {job['title']}")
            print(f"   Active: {job['is_active']}")
            print(f"   Classification: {job.get('title_classification')}")
