#!/usr/bin/env python3
"""Check GeoDynamics job"""

from database.client import db
from datetime import datetime

# Find GeoDynamics ML/AI job
result = db.client.table("job_ranking_view")\
    .select("id, title, company_name, posted_date, posted_date_corrected")\
    .ilike("title", "%Software Engineer ML%")\
    .ilike("company_name", "%GeoDynamics%")\
    .execute()

if result.data:
    for job in result.data:
        print(f"\n🔍 GeoDynamics Job:")
        print(f"   ID: {job['id']}")
        print(f"   Title: {job['title']}")
        print(f"   Company: {job['company_name']}")
        print(f"   Posted Date: {job['posted_date']}")
        print(f"   Posted Date Corrected: {job['posted_date_corrected']}")
        
        # Check if posted_date_corrected is None
        if not job['posted_date_corrected']:
            print(f"\n   ❌ posted_date_corrected is NULL!")
            print(f"   This means the view is not returning the corrected date.")
        else:
            from dateutil import parser as date_parser
            corrected = date_parser.isoparse(job['posted_date_corrected'])
            age_days = (datetime.now(corrected.tzinfo) - corrected).days
            print(f"\n   Age (corrected): {age_days} days")
            print(f"   Expected freshness: 40 (not 150!)")
else:
    print("❌ GeoDynamics job not found")
