#!/usr/bin/env python3
"""Debug why specific jobs are not being loaded"""

from database.client import db
from ranking.job_ranker import JobData, parse_datetime
import json

problem_job_ids = [
    "7ec45673-ce07-4898-b1c8-fbc3383684f6",  # Senior Product Owner
    "bc38bc96-a4d7-4b0e-90c3-4fd065ff0009",  # Data-analist
]

print("\n🔍 Debugging job loading for problem jobs...\n")

for job_id in problem_job_ids:
    print(f"\n{'='*60}")
    print(f"Job ID: {job_id}")
    
    # Get job from view
    result = db.client.table("job_ranking_view")\
        .select("*")\
        .eq("id", job_id)\
        .execute()
    
    if not result.data:
        print("❌ Job NOT in job_ranking_view")
        continue
    
    row = result.data[0]
    print(f"✅ Job found in view: {row['title']}")
    
    # Try to create JobData object
    try:
        # Check if FAANG
        faang_companies = ['google', 'microsoft', 'meta', 'amazon', 'apple', 'netflix', 'facebook', 'alphabet']
        is_faang = row.get('company_name', '').lower() in faang_companies
        
        # Parse labels JSON for seniority
        labels = row.get('labels')
        if isinstance(labels, str):
            try:
                labels = json.loads(labels)
            except:
                labels = {}
        
        seniority = None
        if labels:
            # Try different language keys for seniority
            for lang in ['nl', 'en', 'fr']:
                if lang in labels:
                    seniority_value = labels[lang].get('seniority')
                    if seniority_value:
                        # Handle both string and list
                        if isinstance(seniority_value, list):
                            seniority = seniority_value[0] if seniority_value else None
                        else:
                            seniority = seniority_value
                        break
        
        job = JobData(
            id=row['id'],
            title=row['title'],
            company_id=row['company_id'],
            company_name=row.get('company_name', ''),
            location_id=row['location_id'],
            posted_date=parse_datetime(row.get('posted_date')),
            posted_date_corrected=parse_datetime(row.get('posted_date_corrected')),
            seniority_level=row.get('seniority_level'),
            employment_type=row.get('employment_type'),
            function_areas=row.get('function_areas'),
            base_salary_min=row.get('base_salary_min'),
            base_salary_max=row.get('base_salary_max'),
            apply_url=row.get('apply_url'),
            num_applicants=row.get('num_applicants'),
            is_active=row.get('is_active', True),
            title_classification=row.get('title_classification', 'Data'),
            
            # Company data
            company_industry=row.get('company_industry'),
            company_url=row.get('company_url'),
            company_logo_data=row.get('company_logo_data'),
            company_employee_count_range=row.get('company_employee_count_range'),
            company_rating=row.get('company_rating'),
            company_reviews_count=row.get('company_reviews_count'),
            hiring_model=row.get('hiring_model'),
            is_faang=is_faang,
            
            # Location data
            location_city=row.get('location_city'),
            
            # Enrichment data
            skills_must_have=row.get('skills_must_have'),
            samenvatting_kort=row.get('samenvatting_kort'),
            samenvatting_lang=row.get('samenvatting_lang'),
            data_role_type=row.get('data_role_type'),
            seniority=seniority,
            enrichment_completed_at=parse_datetime(row.get('enrichment_completed_at')),
            
            # Scraping data
            scraped_at=None,
            
            # Tech stack data
            must_have_programmeertalen=row.get('must_have_programmeertalen', []),
            nice_to_have_programmeertalen=row.get('nice_to_have_programmeertalen', []),
            must_have_ecosystemen=row.get('must_have_ecosystemen', []),
            nice_to_have_ecosystemen=row.get('nice_to_have_ecosystemen', []),
            
            # Description data
            description_text=row.get('description_text')
        )
        
        print(f"✅ JobData created successfully")
        print(f"   Classification: {job.title_classification}")
        print(f"   Is active: {job.is_active}")
        print(f"   Posted date: {job.posted_date}")
        print(f"   Posted date corrected: {job.posted_date_corrected}")
        
    except Exception as e:
        print(f"❌ ERROR creating JobData: {e}")
        import traceback
        traceback.print_exc()
