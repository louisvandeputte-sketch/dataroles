#!/usr/bin/env python3
"""Test loading a single job to see enrichment data"""
import sys
sys.path.insert(0, '/Users/louisvandeputte/datarole')

from ranking.job_ranker import load_jobs_from_database
from loguru import logger

# Load all jobs
jobs = load_jobs_from_database()

# Find the specific job
target_job = None
for job in jobs:
    if "Technical power BI consultant" in job.title:
        target_job = job
        break

if target_job:
    print(f"✅ Found job: {target_job.title}")
    print(f"Job ID: {target_job.id}")
    print(f"enrichment_completed_at: {target_job.enrichment_completed_at}")
    print(f"data_role_type: {target_job.data_role_type}")
    print(f"samenvatting_kort: {target_job.samenvatting_kort[:50] if target_job.samenvatting_kort else None}...")
    print(f"\nBase score will be -9999: {not target_job.enrichment_completed_at}")
else:
    print("❌ Job not found")
