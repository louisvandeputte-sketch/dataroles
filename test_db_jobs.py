#!/usr/bin/env python3
"""
Simple test to check database jobs
"""
import sys
sys.path.insert(0, '/Users/louisvandeputte/datarole')

from database.client import get_session
from database.models import Job

if __name__ == "__main__":
    print("Testing database job count...")
    
    session = get_session()
    
    # Count total jobs
    total = session.query(Job).count()
    print(f"Total jobs in database: {total}")
    
    # Count by source
    linkedin = session.query(Job).filter(Job.source == 'linkedin').count()
    indeed = session.query(Job).filter(Job.source == 'indeed').count()
    
    print(f"  LinkedIn: {linkedin}")
    print(f"  Indeed: {indeed}")
    
    # Sample a few jobs
    if total > 0:
        print("\nSample jobs:")
        jobs = session.query(Job).limit(3).all()
        for job in jobs:
            print(f"  - {job.title} at {job.company} (source: {job.source}, active: {job.is_active})")
    
    session.close()
