#!/usr/bin/env python3
"""
Check how many jobs would be deleted before 18/10/2025.
This is a dry-run script that doesn't delete anything.
"""

from database.client import db
from loguru import logger


def check_old_jobs(cutoff_date: str = "2025-10-18"):
    """Check how many jobs would be deleted."""
    
    print(f"🔍 Checking jobs posted before {cutoff_date}")
    print("=" * 60)
    
    try:
        # Count jobs to be deleted
        old_jobs = db.client.table("job_postings")\
            .select("id, title, posted_date, company_id")\
            .lt("posted_date", cutoff_date)\
            .order("posted_date", desc=False)\
            .limit(10)\
            .execute()
        
        # Get total count
        count_result = db.client.table("job_postings")\
            .select("id", count="exact")\
            .lt("posted_date", cutoff_date)\
            .execute()
        
        total_old = count_result.count if count_result.count else 0
        
        # Get total jobs
        total_result = db.client.table("job_postings")\
            .select("id", count="exact")\
            .execute()
        
        total_jobs = total_result.count if total_result.count else 0
        
        print(f"\n📊 Statistics:")
        print(f"   Total jobs in database: {total_jobs}")
        print(f"   Jobs before {cutoff_date}: {total_old}")
        print(f"   Jobs that would remain: {total_jobs - total_old}")
        print(f"   Percentage to delete: {(total_old / total_jobs * 100):.1f}%" if total_jobs > 0 else "   Percentage to delete: 0%")
        
        if old_jobs.data and len(old_jobs.data) > 0:
            print(f"\n📋 Sample of oldest jobs (showing first 10):")
            print("-" * 60)
            for job in old_jobs.data:
                posted = job.get('posted_date', 'Unknown')[:10] if job.get('posted_date') else 'Unknown'
                title = job.get('title', 'No title')[:50]
                print(f"   {posted} - {title}")
        
        print("\n" + "=" * 60)
        print(f"✅ Check complete. {total_old} jobs would be deleted.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    import sys
    
    cutoff_date = sys.argv[1] if len(sys.argv) > 1 else "2025-10-18"
    check_old_jobs(cutoff_date)
