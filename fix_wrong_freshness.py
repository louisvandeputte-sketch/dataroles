#!/usr/bin/env python3
"""Fix jobs with wrong freshness score (F:150 but old corrected date)"""

from database.client import db
from datetime import datetime, timedelta
from dateutil import parser as date_parser

print("🔍 Finding jobs with wrong freshness scores...")

# Get jobs with F:150 from metadata
result = db.client.table("job_postings")\
    .select("id, title, posted_date, posted_date_corrected, ranking_metadata, base_score")\
    .not_.is_("ranking_metadata", "null")\
    .not_.is_("posted_date_corrected", "null")\
    .limit(1000)\
    .execute()

wrong_jobs = []
for job in result.data:
    metadata = job.get('ranking_metadata', {})
    freshness = metadata.get('freshness_score')
    
    if freshness == 150:  # Has MEGA BOOST
        # Check if corrected date is actually old
        corrected = date_parser.isoparse(job['posted_date_corrected'])
        age = datetime.now(corrected.tzinfo) - corrected
        hours_old = age.total_seconds() / 3600
        
        if hours_old > 30:  # Should NOT have F:150!
            wrong_jobs.append({
                'id': job['id'],
                'title': job['title'],
                'age_days': age.days,
                'hours_old': hours_old,
                'current_freshness': freshness,
                'correct_freshness': 40 if age.days <= 30 else 20
            })

print(f"\n📊 Found {len(wrong_jobs)} jobs with wrong freshness scores")

if wrong_jobs:
    print(f"\n🔧 Fixing first 10 jobs:")
    for job in wrong_jobs[:10]:
        print(f"\n   {job['title'][:50]}")
        print(f"   Age: {job['age_days']} days ({job['hours_old']:.0f} hours)")
        print(f"   Current F:{job['current_freshness']} → Correct F:{job['correct_freshness']}")
        
        # Calculate correct base score
        # We need to recalculate with correct freshness
        # For now, just mark these jobs for re-ranking
        db.client.table("job_postings").update({
            'needs_ranking': True
        }).eq('id', job['id']).execute()
    
    print(f"\n✅ Marked {min(10, len(wrong_jobs))} jobs for re-ranking")
    print(f"   Total wrong jobs: {len(wrong_jobs)}")
    print(f"\n💡 Run ranking again to fix all scores")
