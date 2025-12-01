#!/usr/bin/env python3
"""Full debug of job ranking for problematic job"""

from database.client import db
from ranking.job_ranker import JobRankingSystem, JobData, parse_datetime
from loguru import logger
import json

print("\n🔍 Full Debug of Job Ranking...\n")

# Get the problematic job from view
job_title = "Technical Solution Architect (Data Platform)"
row = db.client.table("job_ranking_view")\
    .select("*")\
    .eq("title", job_title)\
    .single()\
    .execute().data

print(f"✅ Found job in view: {row['title']}")
print(f"   ID: {row['id']}")
print(f"   Posted: {row.get('posted_date')}")
print(f"   Posted corrected: {row.get('posted_date_corrected')}")
print(f"   Enrichment completed: {row.get('enrichment_completed_at')}")
print(f"   Classification: {row.get('title_classification')}")
print(f"   is_active: {row.get('is_active')}")

# Manually create JobData object (same as load_jobs_from_database)
print("\n" + "="*80)
print("Creating JobData object...")
print("="*80)

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
        for lang in ['nl', 'en', 'fr']:
            if lang in labels:
                seniority_value = labels[lang].get('seniority')
                if seniority_value:
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
        company_industry=row.get('company_industry'),
        company_url=row.get('company_url'),
        company_logo_data=row.get('company_logo_data'),
        company_employee_count_range=row.get('company_employee_count_range'),
        company_rating=row.get('company_rating'),
        company_reviews_count=row.get('company_reviews_count'),
        hiring_model=row.get('hiring_model'),
        is_faang=is_faang,
        location_city=row.get('location_city'),
        skills_must_have=row.get('skills_must_have'),
        samenvatting_kort=row.get('samenvatting_kort'),
        samenvatting_lang=row.get('samenvatting_lang'),
        data_role_type=row.get('data_role_type'),
        seniority=seniority,
        enrichment_completed_at=parse_datetime(row.get('enrichment_completed_at')),
        scraped_at=None,
        must_have_programmeertalen=row.get('must_have_programmeertalen', []),
        nice_to_have_programmeertalen=row.get('nice_to_have_programmeertalen', []),
        must_have_ecosystemen=row.get('must_have_ecosystemen', []),
        nice_to_have_ecosystemen=row.get('nice_to_have_ecosystemen', []),
        description_text=row.get('description_text')
    )
    
    print(f"✅ JobData created successfully!")
    print(f"   is_active: {job.is_active}")
    print(f"   enrichment_completed_at: {job.enrichment_completed_at}")
    print(f"   posted_date_corrected: {job.posted_date_corrected}")
    
    # Now try to rank it
    print("\n" + "="*80)
    print("Ranking job...")
    print("="*80)
    
    ranker = JobRankingSystem()
    ranked = ranker.rank_jobs([job])
    
    if ranked:
        r = ranked[0]
        print(f"\n✅ Ranking SUCCESSFUL!")
        print(f"   Freshness: {r.freshness_score:.2f}")
        print(f"   Quality: {r.quality_score:.2f}")
        print(f"   Transparency: {r.transparency_score:.2f}")
        print(f"   Role match: {r.role_match_score:.2f}")
        print(f"   Completeness: {r.completeness_score:.2f}")
        print(f"   Reputation: {r.reputation_score:.2f}")
        print(f"   Base score: {r.base_score:.2f}")
        print(f"   Hourly multiplier: {r.hourly_multiplier:.3f}")
        print(f"   Final score: {r.final_score:.2f}")
        print(f"   Final rank: {r.final_rank}")
    else:
        print(f"\n❌ Ranking returned empty list!")
        
except Exception as e:
    logger.error(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
