#!/usr/bin/env python3
"""Debug AXA job ranking data"""

from database.client import db
from datetime import datetime

# Find AXA AI Analyst job
result = db.client.table("job_ranking_view")\
    .select("id, title, company_name, posted_date, posted_date_corrected")\
    .ilike("title", "%AI Analyst%")\
    .ilike("company_name", "%AXA%")\
    .limit(1)\
    .execute()

if result.data:
    job = result.data[0]
    print(f"\n🔍 AXA AI Analyst Job Data:")
    print(f"   ID: {job['id']}")
    print(f"   Title: {job['title']}")
    print(f"   Company: {job['company_name']}")
    print(f"   Posted Date: {job['posted_date']}")
    print(f"   Posted Date Corrected: {job['posted_date_corrected']}")
    
    if job['posted_date_corrected']:
        corrected = datetime.fromisoformat(job['posted_date_corrected'].replace('Z', '+00:00'))
        age_days = (datetime.now(corrected.tzinfo) - corrected).days
        print(f"   Age (corrected): {age_days} days")
    
    # Check job_postings table for ranking data
    ranking = db.client.table("job_postings")\
        .select("base_score, ranking_score, ranking_position, ranking_metadata, hourly_multiplier, ranking_updated_at")\
        .eq("id", job['id'])\
        .single()\
        .execute()
    
    if ranking.data:
        print(f"\n📊 Ranking Data (from job_postings):")
        print(f"   Rank: {ranking.data['ranking_position']}")
        print(f"   Base Score: {ranking.data['base_score']}")
        print(f"   Ranking Score: {ranking.data['ranking_score']}")
        print(f"   Hourly Multiplier: {ranking.data['hourly_multiplier']}")
        print(f"   Updated At: {ranking.data['ranking_updated_at']}")
        
        if ranking.data['ranking_metadata']:
            meta = ranking.data['ranking_metadata']
            print(f"\n   Metadata:")
            print(f"   - Freshness: {meta.get('freshness_score')}")
            print(f"   - Quality: {meta.get('quality_score')}")
            print(f"   - Transparency: {meta.get('transparency_score')}")
            print(f"   - Role Match: {meta.get('role_match_score')}")
else:
    print("❌ AXA AI Analyst job not found")
