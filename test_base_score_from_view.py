#!/usr/bin/env python3
"""Test base score calculation directly from view"""
import sys
sys.path.insert(0, '/Users/louisvandeputte/datarole')

from database.client import db
from datetime import datetime
from dateutil import parser as date_parser

# Weights
WEIGHT_FRESHNESS = 0.25
WEIGHT_QUALITY = 0.20
WEIGHT_TRANSPARENCY = 0.20
WEIGHT_ROLE_MATCH = 0.15
WEIGHT_COMPLETENESS = 0.10
WEIGHT_REPUTATION = 0.10

def calculate_base_score(row):
    """Calculate base score from view row"""
    
    # 1. FRESHNESS (25%)
    freshness = 0
    if row.get('posted_date'):
        posted = date_parser.parse(row['posted_date'])
        if posted.tzinfo:
            posted = posted.replace(tzinfo=None)
        days_old = (datetime.now() - posted).days
        if days_old <= 7:
            freshness = 100
        elif days_old <= 14:
            freshness = 75
        elif days_old <= 30:
            freshness = 50
        else:
            freshness = max(0, 50 - (days_old - 30))
    
    # 2. QUALITY (20%)
    quality = 0
    # Skills
    skills = row.get('skills_must_have') or []
    if isinstance(skills, list) and len(skills) >= 3:
        quality += 20
    elif not skills or len(skills) == 0:
        quality -= 30  # PENALTY
    
    # Salary
    if row.get('base_salary_min') and row.get('base_salary_max'):
        quality += 25
    
    # Seniority
    if row.get('seniority_level'):
        quality += 15
    
    # Employment type
    if row.get('employment_type'):
        quality += 10
    
    # Samenvatting
    if row.get('samenvatting_lang'):
        quality += 15
    
    # Description
    desc = row.get('description_text') or ''
    if len(desc) > 500:
        quality += 10
    
    # Tech stack bonus
    tech_count = 0
    for field in ['must_have_programmeertalen', 'nice_to_have_programmeertalen',
                  'must_have_ecosystemen', 'nice_to_have_ecosystemen']:
        items = row.get(field) or []
        if isinstance(items, list):
            tech_count += len(items)
    quality += min(15, tech_count)
    
    quality = min(100, quality)
    
    # 3. TRANSPARENCY (20%)
    transparency = 0
    if row.get('hiring_model') == 'direct':
        transparency += 60
    if row.get('apply_url'):
        transparency += 20
    if row.get('num_applicants') is not None:
        transparency += 10
    if row.get('company_logo_data'):
        transparency += 10
    
    # 4. ROLE MATCH (15%)
    role_match = 10  # default
    role_type = row.get('data_role_type')
    if role_type in ['Data Engineer', 'Data Scientist', 'Data Analyst', 
                     'ML Engineer', 'BI Developer', 'Analytics Engineer']:
        role_match = 100
    elif role_type == 'Other':
        role_match = -200  # EXTREME PENALTY
    elif role_type == 'NIS':
        role_match = -99999  # MASSIVE PENALTY - NIS jobs always at bottom
    
    # 5. COMPLETENESS (10%)
    completeness = 0
    if row.get('samenvatting_kort'):
        completeness += 40
    if row.get('company_industry'):
        completeness += 20
    if row.get('location_city'):
        completeness += 20
    if row.get('function_areas'):
        completeness += 20
    
    # 6. REPUTATION (10%)
    reputation = 0
    rating = row.get('company_rating')
    if rating:
        if rating >= 4.0:
            reputation += 60
        elif rating >= 3.5:
            reputation += 40
        elif rating >= 3.0:
            reputation += 20
    
    reviews = row.get('company_reviews_count')
    if reviews and reviews >= 50:
        reputation += 20
    elif reviews and reviews >= 10:
        reputation += 10
    
    # Check FAANG
    company_name = (row.get('company_name') or '').lower()
    faang = ['google', 'microsoft', 'meta', 'amazon', 'apple', 'netflix']
    if any(f in company_name for f in faang):
        reputation += 20
    
    # CALCULATE BASE SCORE
    base_score = (
        freshness * WEIGHT_FRESHNESS +
        quality * WEIGHT_QUALITY +
        transparency * WEIGHT_TRANSPARENCY +
        role_match * WEIGHT_ROLE_MATCH +
        completeness * WEIGHT_COMPLETENESS +
        reputation * WEIGHT_REPUTATION
    )
    
    # EXTREME PENALTY for non-enriched
    if not row.get('enrichment_completed_at'):
        base_score = -9999
    
    return {
        'base_score': round(base_score, 2),
        'freshness': freshness,
        'quality': quality,
        'transparency': transparency,
        'role_match': role_match,
        'completeness': completeness,
        'reputation': reputation
    }

# Test with a few jobs
print("Testing base score calculation from view...\n")

result = db.client.table("job_ranking_view")\
    .select("*")\
    .limit(5)\
    .execute()

for row in result.data:
    scores = calculate_base_score(row)
    print(f"Job: {row['title'][:50]}")
    print(f"  Company: {row.get('company_name')}")
    print(f"  Base Score: {scores['base_score']}")
    print(f"    F:{scores['freshness']} Q:{scores['quality']} T:{scores['transparency']}")
    print(f"    R:{scores['role_match']} C:{scores['completeness']} Rep:{scores['reputation']}")
    print(f"  Enriched: {bool(row.get('enrichment_completed_at'))}")
    print()
