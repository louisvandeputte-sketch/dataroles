#!/usr/bin/env python3
"""
Delete all jobs posted before 18/10/2025.

This script will:
1. Find all jobs with posted_date < 2025-10-18
2. Delete them from the database (CASCADE will handle related tables)
3. Show statistics about deleted jobs
"""

from datetime import datetime
from database.client import db
from loguru import logger

# Configure logger
logger.add("logs/delete_old_jobs_{time}.log", rotation="10 MB")


def delete_old_jobs(cutoff_date: str = "2025-10-18"):
    """
    Delete all jobs posted before the cutoff date.
    
    Args:
        cutoff_date: Date in YYYY-MM-DD format (default: 2025-10-18)
    """
    logger.info(f"Starting deletion of jobs posted before {cutoff_date}")
    
    try:
        # First, get count of jobs to be deleted
        count_result = db.client.table("job_postings")\
            .select("id", count="exact")\
            .lt("posted_date", cutoff_date)\
            .execute()
        
        total_to_delete = count_result.count if count_result.count else 0
        
        if total_to_delete == 0:
            logger.info("No jobs found to delete")
            print("✅ No jobs found posted before", cutoff_date)
            return
        
        logger.info(f"Found {total_to_delete} jobs to delete")
        print(f"Found {total_to_delete} jobs posted before {cutoff_date}")
        
        # Confirm deletion
        confirm = input(f"\n⚠️  Are you sure you want to delete {total_to_delete} jobs? (yes/no): ")
        if confirm.lower() != "yes":
            logger.info("Deletion cancelled by user")
            print("❌ Deletion cancelled")
            return
        
        # Delete jobs (CASCADE will handle related tables automatically)
        logger.info("Starting deletion...")
        print("\n🗑️  Deleting jobs...")
        
        delete_result = db.client.table("job_postings")\
            .delete()\
            .lt("posted_date", cutoff_date)\
            .execute()
        
        deleted_count = len(delete_result.data) if delete_result.data else 0
        
        logger.success(f"Successfully deleted {deleted_count} jobs")
        print(f"✅ Successfully deleted {deleted_count} jobs posted before {cutoff_date}")
        
        # Show some statistics
        remaining_result = db.client.table("job_postings")\
            .select("id", count="exact")\
            .execute()
        
        remaining_count = remaining_result.count if remaining_result.count else 0
        
        print(f"\n📊 Statistics:")
        print(f"   - Jobs deleted: {deleted_count}")
        print(f"   - Jobs remaining: {remaining_count}")
        
        logger.info(f"Deletion complete. {deleted_count} deleted, {remaining_count} remaining")
        
    except Exception as e:
        logger.error(f"Error during deletion: {e}")
        print(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    import sys
    
    # Allow custom cutoff date as command line argument
    cutoff_date = sys.argv[1] if len(sys.argv) > 1 else "2025-10-18"
    
    print(f"🗑️  Job Deletion Script")
    print(f"=" * 50)
    print(f"Cutoff date: {cutoff_date}")
    print(f"Jobs posted BEFORE this date will be deleted")
    print(f"=" * 50)
    print()
    
    delete_old_jobs(cutoff_date)
