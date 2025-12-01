#!/usr/bin/env python3
"""Diagnose why some jobs have no ranking scores"""

from database.client import db
from datetime import datetime, timedelta

print("\n🔍 Diagnosing Missing Ranking Scores...\n")

# Get recent jobs (last 7 days)
week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()

print("="*80)
print("📊 Recent Jobs (Last 7 Days)")
print("="*80)

jobs = db.client.table("job_postings")\
    .select("id, title, source, posted_date, is_active")\
    .gte("posted_date", week_ago)\
    .eq("is_active", True)\
    .order("posted_date", desc=True)\
    .limit(50)\
    .execute()

print(f"Found {len(jobs.data)} recent active jobs\n")

# Check rankings for these jobs
print("="*80)
print("🎯 Checking Rankings")
print("="*80)

jobs_with_ranking = 0
jobs_without_ranking = 0
jobs_without_ranking_list = []

for job in jobs.data:
    job_id = job['id']
    
    # Check if ranking exists
    ranking = db.client.table("job_ranking_view")\
        .select("*")\
        .eq("job_posting_id", job_id)\
        .execute()
    
    if ranking.data:
        jobs_with_ranking += 1
    else:
        jobs_without_ranking += 1
        jobs_without_ranking_list.append({
            'id': job_id,
            'title': job['title'],
            'source': job.get('source', 'N/A'),
            'posted_date': job.get('posted_date', 'N/A')
        })

print(f"\n✅ Jobs WITH ranking: {jobs_with_ranking}")
print(f"❌ Jobs WITHOUT ranking: {jobs_without_ranking}")

if jobs_without_ranking > 0:
    print(f"\n⚠️ {jobs_without_ranking} jobs are missing rankings!\n")
    print("Jobs without rankings:")
    for job in jobs_without_ranking_list[:10]:
        print(f"  - {job['title'][:50]:50} | {job['source']:8} | {job['posted_date']}")

print("\n" + "="*80)
print("🔍 Checking Ranking Calculation Schedule")
print("="*80)

# Check when rankings were last calculated
rankings = db.client.table("job_ranking_view")\
    .select("calculated_at")\
    .order("calculated_at", desc=True)\
    .limit(1)\
    .execute()

if rankings.data:
    last_calc = rankings.data[0]['calculated_at']
    print(f"✅ Last ranking calculation: {last_calc}")
    
    # Parse and check if recent
    last_calc_dt = datetime.fromisoformat(last_calc.replace('Z', '+00:00'))
    now = datetime.utcnow().replace(tzinfo=last_calc_dt.tzinfo)
    hours_ago = (now - last_calc_dt).total_seconds() / 3600
    
    print(f"   ({hours_ago:.1f} hours ago)")
    
    if hours_ago > 2:
        print(f"   ⚠️ Rankings are STALE! Should run every hour.")
    else:
        print(f"   ✅ Rankings are recent")
else:
    print("❌ NO rankings found in database!")

print("\n" + "="*80)
print("🔍 Checking Job Enrichment Status")
print("="*80)

# Check if jobs without rankings have enrichment data
if jobs_without_ranking_list:
    print("\nChecking enrichment for jobs without rankings:")
    
    for job in jobs_without_ranking_list[:5]:
        enrichment = db.client.table("llm_enrichment")\
            .select("*")\
            .eq("job_posting_id", job['id'])\
            .execute()
        
        if enrichment.data:
            enr = enrichment.data[0]
            print(f"\n  {job['title'][:40]:40}")
            print(f"    ✅ Has enrichment")
            print(f"    - Quality: {enr.get('quality_score', 'N/A')}")
            print(f"    - Title match: {enr.get('title_match_score', 'N/A')}")
            print(f"    - Relevance: {enr.get('relevance_score', 'N/A')}")
        else:
            print(f"\n  {job['title'][:40]:40}")
            print(f"    ❌ NO enrichment data!")

print("\n" + "="*80)
print("🎯 DIAGNOSIS")
print("="*80)

if jobs_without_ranking > 0:
    print(f"\n❌ PROBLEM: {jobs_without_ranking} jobs have NO ranking scores")
    print("\nPossible causes:")
    print("1. Ranking scheduler not running")
    print("2. Jobs added after last ranking calculation")
    print("3. Jobs missing enrichment data (required for ranking)")
    print("4. Ranking calculation failing silently")
    print("\nRecommended actions:")
    print("1. Check if ranking scheduler is running")
    print("2. Manually trigger ranking calculation")
    print("3. Check logs for ranking calculation errors")
    print("4. Verify all jobs have enrichment data")
else:
    print("\n✅ All recent jobs have ranking scores!")

print("\n" + "="*80)
