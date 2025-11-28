#!/usr/bin/env python3
"""Check if job_ranking_view has posted_date_corrected"""

from database.client import db

# Check if the view has the column
result = db.client.table("job_ranking_view")\
    .select("id, posted_date, posted_date_corrected")\
    .limit(5)\
    .execute()

print(f"\n🔍 First 5 jobs from job_ranking_view:")
for job in result.data:
    print(f"   ID: {job['id'][:8]}... | posted_date: {job.get('posted_date')} | posted_date_corrected: {job.get('posted_date_corrected')}")

# Count how many have posted_date_corrected
count_result = db.client.table("job_ranking_view")\
    .select("id", count="exact")\
    .not_.is_("posted_date_corrected", "null")\
    .execute()

print(f"\n📊 Jobs with posted_date_corrected: {count_result.count}")
