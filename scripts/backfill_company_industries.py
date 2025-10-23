"""
Backfill company industry data from job postings.
This script extracts industry information from job postings and updates the companies table.
"""

from database.client import db
from loguru import logger
from collections import Counter

def backfill_company_industries():
    """Backfill company industry from job postings."""
    
    # Get all companies without industry data
    companies = db.client.table("companies")\
        .select("id, name, industry")\
        .is_("industry", "null")\
        .execute()
    
    logger.info(f"Found {len(companies.data)} companies without industry data")
    
    updated_count = 0
    skipped_count = 0
    
    for company in companies.data:
        company_id = company['id']
        company_name = company['name']
        
        # Get all job postings for this company with industry data
        jobs = db.client.table("job_postings")\
            .select("industries")\
            .eq("company_id", company_id)\
            .not_.is_("industries", "null")\
            .execute()
        
        if not jobs.data:
            skipped_count += 1
            continue
        
        # Collect all industries from all jobs
        all_industries = []
        for job in jobs.data:
            industries = job.get('industries')
            if industries:
                # industries can be a string or array
                if isinstance(industries, str):
                    all_industries.append(industries)
                elif isinstance(industries, list):
                    all_industries.extend(industries)
        
        if not all_industries:
            skipped_count += 1
            continue
        
        # Find most common industry
        industry_counts = Counter(all_industries)
        most_common_industry = industry_counts.most_common(1)[0][0]
        
        # Update company
        try:
            db.client.table("companies")\
                .update({"industry": most_common_industry})\
                .eq("id", company_id)\
                .execute()
            
            updated_count += 1
            logger.info(f"✓ {company_name}: {most_common_industry} (from {len(jobs.data)} jobs)")
        except Exception as e:
            logger.error(f"Failed to update {company_name}: {e}")
    
    logger.success(f"✅ Backfill complete: {updated_count} updated, {skipped_count} skipped (no industry data)")
    return {
        "updated": updated_count,
        "skipped": skipped_count
    }


if __name__ == "__main__":
    logger.info("Starting company industry backfill...")
    result = backfill_company_industries()
    logger.info(f"Final result: {result}")
