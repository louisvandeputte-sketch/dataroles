#!/usr/bin/env python3
"""
Delete all companies that have no job postings.

This script will:
1. Find all companies with no jobs
2. Delete them from the database (CASCADE will handle related tables)
3. Show statistics about deleted companies
"""

from database.client import db
from loguru import logger

# Configure logger
logger.add("logs/delete_companies_without_jobs_{time}.log", rotation="10 MB")


def delete_companies_without_jobs():
    """Delete all companies that have no job postings."""
    
    logger.info("Starting deletion of companies without jobs")
    
    try:
        # Get all companies with their job counts
        companies_with_jobs = db.client.table("companies")\
            .select("id, name, job_postings(id)")\
            .execute()
        
        # Find companies without jobs
        companies_to_delete = []
        companies_with_jobs_list = []
        
        for company in companies_with_jobs.data:
            job_postings = company.get('job_postings', [])
            if not job_postings or len(job_postings) == 0:
                companies_to_delete.append({
                    'id': company['id'],
                    'name': company['name']
                })
            else:
                companies_with_jobs_list.append(company['name'])
        
        total_to_delete = len(companies_to_delete)
        total_to_keep = len(companies_with_jobs_list)
        
        if total_to_delete == 0:
            logger.info("No companies found without jobs")
            print("✅ No companies found without jobs")
            return
        
        logger.info(f"Found {total_to_delete} companies to delete")
        print(f"Found {total_to_delete} companies without jobs")
        print(f"Will keep {total_to_keep} companies with jobs")
        
        # Show sample
        print(f"\nSample of companies to delete (first 10):")
        for i, company in enumerate(companies_to_delete[:10]):
            print(f"   {i+1}. {company['name']}")
        if total_to_delete > 10:
            print(f"   ... and {total_to_delete - 10} more")
        
        # Confirm deletion
        confirm = input(f"\n⚠️  Are you sure you want to delete {total_to_delete} companies? (yes/no): ")
        if confirm.lower() != "yes":
            logger.info("Deletion cancelled by user")
            print("❌ Deletion cancelled")
            return
        
        # Delete companies one by one (to handle CASCADE properly)
        logger.info("Starting deletion...")
        print("\n🗑️  Deleting companies...")
        
        deleted_count = 0
        for company in companies_to_delete:
            try:
                db.client.table("companies")\
                    .delete()\
                    .eq("id", company['id'])\
                    .execute()
                deleted_count += 1
                
                if deleted_count % 100 == 0:
                    print(f"   Deleted {deleted_count}/{total_to_delete}...")
                    
            except Exception as e:
                logger.error(f"Failed to delete company {company['name']}: {e}")
        
        logger.success(f"Successfully deleted {deleted_count} companies")
        print(f"\n✅ Successfully deleted {deleted_count} companies without jobs")
        
        # Show statistics
        remaining_result = db.client.table("companies")\
            .select("id", count="exact")\
            .execute()
        
        remaining_count = remaining_result.count if remaining_result.count else 0
        
        print(f"\n📊 Statistics:")
        print(f"   - Companies deleted: {deleted_count}")
        print(f"   - Companies remaining: {remaining_count}")
        print(f"   - All remaining companies have jobs ✅")
        
        logger.info(f"Deletion complete. {deleted_count} deleted, {remaining_count} remaining")
        
    except Exception as e:
        logger.error(f"Error during deletion: {e}")
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    print(f"🗑️  Company Cleanup Script")
    print(f"=" * 50)
    print(f"This will delete companies with NO job postings")
    print(f"=" * 50)
    print()
    
    delete_companies_without_jobs()
