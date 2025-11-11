#!/usr/bin/env python3
"""Test Indeed job processing."""

import asyncio
from models.indeed import IndeedJobPosting
from ingestion.processor import process_job_posting
from uuid import uuid4

# Sample Indeed job from API
test_job = {
    "jobid": "881887fe0ea6ded4",
    "job_title": "Senior Accountant",
    "company_name": "Tanner Pharma Group",
    "location": "Charlotte, NC",
    "url": "https://www.indeed.com/viewjob?jk=881887fe0ea6ded4",
    "description_text": "Job Description: We are seeking a Senior Accountant...",
    "job_type": "Full-time",
    "salary_formatted": "$50,000 - $70,000 a year",
    "date_posted": "30+ days ago",
    "date_posted_parsed": "2024-10-10T00:00:00Z",
    "benefits": ["Health insurance", "401(k)"],
    "qualifications": "Bachelor's degree in Accounting required",
    "company_rating": "4.2",
    "company_reviews_count": "150",
    "logo_url": "https://example.com/logo.png"
}

print("Testing Indeed job processing...")
print("=" * 80)

try:
    # Parse with Pydantic model
    print("\n1. Parsing with IndeedJobPosting model...")
    job = IndeedJobPosting(**test_job)
    print(f"   ✅ Parsed successfully")
    print(f"   Job ID: {job.jobid}")
    print(f"   Title: {job.job_title}")
    print(f"   Company: {job.company_name}")
    
    # Test company dict
    print("\n2. Getting company dict...")
    company_dict = job.get_company_dict()
    print(f"   ✅ Company dict: {company_dict}")
    
    # Test location string
    print("\n3. Getting location string...")
    location_str = job.get_location_string()
    print(f"   ✅ Location: {location_str}")
    
    # Test processing
    print("\n4. Processing job posting...")
    scrape_run_id = uuid4()
    result = process_job_posting(test_job, scrape_run_id, source="indeed")
    
    print(f"   Status: {result.status}")
    print(f"   Job ID: {result.job_id}")
    print(f"   Error: {result.error}")
    
    if result.status == "success":
        print("   ✅ Processing successful!")
    else:
        print(f"   ❌ Processing failed: {result.error}")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
