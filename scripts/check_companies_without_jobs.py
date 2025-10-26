#!/usr/bin/env python3
"""
Check which companies have no jobs.
This is a dry-run script that doesn't delete anything.
"""

from database.client import db
from loguru import logger


def check_companies_without_jobs():
    """Check how many companies have no jobs."""
    
    print(f"🔍 Checking companies without jobs")
    print("=" * 60)
    
    try:
        # Get all companies
        all_companies = db.client.table("companies")\
            .select("id, name, linkedin_company_id")\
            .execute()
        
        total_companies = len(all_companies.data) if all_companies.data else 0
        
        # Get companies with jobs (using LEFT JOIN to find companies WITH jobs)
        companies_with_jobs = db.client.table("companies")\
            .select("id, name, job_postings(id)")\
            .execute()
        
        # Count companies that actually have jobs
        companies_with_jobs_count = 0
        companies_without_jobs = []
        
        for company in companies_with_jobs.data:
            job_postings = company.get('job_postings', [])
            if job_postings and len(job_postings) > 0:
                companies_with_jobs_count += 1
            else:
                companies_without_jobs.append({
                    'id': company['id'],
                    'name': company['name']
                })
        
        companies_without_jobs_count = len(companies_without_jobs)
        
        print(f"\n📊 Statistics:")
        print(f"   Total companies: {total_companies}")
        print(f"   Companies with jobs: {companies_with_jobs_count}")
        print(f"   Companies without jobs: {companies_without_jobs_count}")
        print(f"   Percentage without jobs: {(companies_without_jobs_count / total_companies * 100):.1f}%" if total_companies > 0 else "   Percentage without jobs: 0%")
        
        if companies_without_jobs and len(companies_without_jobs) > 0:
            print(f"\n📋 Sample of companies without jobs (showing first 20):")
            print("-" * 60)
            for i, company in enumerate(companies_without_jobs[:20]):
                name = company.get('name', 'No name')[:50]
                print(f"   {i+1}. {name}")
            
            if len(companies_without_jobs) > 20:
                print(f"   ... and {len(companies_without_jobs) - 20} more")
        
        print("\n" + "=" * 60)
        print(f"✅ Check complete. {companies_without_jobs_count} companies have no jobs.")
        
        return companies_without_jobs
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    check_companies_without_jobs()
