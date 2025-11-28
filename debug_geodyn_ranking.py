#!/usr/bin/env python3
"""Debug why GeoDynamics job doesn't get updated"""

from database.client import db
from ranking.job_ranker import load_jobs_from_database
from dateutil import parser as date_parser
from datetime import datetime

print("🔍 Loading all jobs from database...")
jobs = load_jobs_from_database()

# Find GeoDynamics job
geodyn_id = "faf12622-68b4-477e-9ca2-59527485cdb1"
geodyn_job = None

for job in jobs:
    if job.id == geodyn_id:
        geodyn_job = job
        break

if geodyn_job:
    print(f"\n✅ Found GeoDynamics job in loaded jobs!")
    print(f"   ID: {geodyn_job.id}")
    print(f"   Title: {geodyn_job.title}")
    print(f"   Posted Date: {geodyn_job.posted_date}")
    print(f"   Posted Date Corrected: {geodyn_job.posted_date_corrected}")
    
    if geodyn_job.posted_date_corrected:
        age = datetime.now(geodyn_job.posted_date_corrected.tzinfo) - geodyn_job.posted_date_corrected
        hours_old = age.total_seconds() / 3600
        print(f"   Age: {age.days} days ({hours_old:.0f} hours)")
        
        # Calculate expected freshness
        if hours_old <= 30:
            expected_f = 150
        elif age.days <= 1:
            expected_f = 100
        elif age.days <= 3:
            expected_f = 90
        elif age.days <= 7:
            expected_f = 75
        elif age.days <= 14:
            expected_f = 60
        elif age.days <= 30:
            expected_f = 40
        else:
            expected_f = 20
        
        print(f"   Expected Freshness: {expected_f}")
    else:
        print(f"   ⚠️ posted_date_corrected is None!")
        print(f"   Will use posted_date: {geodyn_job.posted_date}")
else:
    print(f"\n❌ GeoDynamics job NOT found in loaded jobs!")
    print(f"   Total jobs loaded: {len(jobs)}")
    
    # Check if it's in the database
    result = db.client.table("job_postings")\
        .select("id, title, is_active")\
        .eq("id", geodyn_id)\
        .single()\
        .execute()
    
    if result.data:
        print(f"\n   Job exists in database:")
        print(f"   - Title: {result.data['title']}")
        print(f"   - Active: {result.data['is_active']}")
