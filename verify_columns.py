#!/usr/bin/env python3
"""Verify all column names for the ranking view"""
import sys
sys.path.insert(0, '/Users/louisvandeputte/datarole')

from database.client import db

tables = {
    'job_postings': ['id', 'title', 'company_id', 'location_id', 'posted_date', 
                     'seniority_level', 'employment_type', 'function_areas', 
                     'base_salary_min', 'base_salary_max', 'apply_url', 
                     'num_applicants', 'is_active', 'title_classification'],
    'companies': ['id', 'name', 'industry', 'company_url', 'logo_data', 
                  'employee_count_range', 'rating', 'reviews_count'],
    'company_master_data': ['company_id', 'hiring_model'],
    'locations': ['id', 'city'],
    'llm_enrichment': ['job_posting_id', 'enrichment_completed_at', 'type_datarol', 
                       'hard_skills', 'samenvatting_kort_nl', 'samenvatting_lang_nl',
                       'must_have_programmeertalen', 'nice_to_have_programmeertalen',
                       'must_have_ecosystemen', 'nice_to_have_ecosystemen', 'labels'],
    'job_descriptions': ['job_posting_id', 'full_description_text']
}

print("Verifying all columns exist in database...\n")

for table_name, columns in tables.items():
    print(f"Checking {table_name}...")
    result = db.client.table(table_name).select('*').limit(1).execute()
    
    if result.data:
        actual_columns = set(result.data[0].keys())
        for col in columns:
            if col in actual_columns:
                print(f"  ✅ {col}")
            else:
                print(f"  ❌ {col} - NOT FOUND")
                print(f"     Available: {sorted(actual_columns)}")
    else:
        print(f"  ⚠️  No data in table")
    print()
