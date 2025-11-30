#!/usr/bin/env python3
"""Investigate jobs without ranking scores"""

from database.client import db

# Get jobs without ranking scores
print("\n🔍 Investigating jobs without ranking scores...\n")

# Query jobs with NULL ranking_score
result = db.client.table("job_postings")\
    .select("id, title, company_id, is_active, title_classification, ranking_score, base_score, ranking_position, needs_ranking, ranking_updated_at")\
    .is_("ranking_score", "null")\
    .eq("is_active", True)\
    .eq("title_classification", "Data")\
    .limit(20)\
    .execute()

print(f"📊 Found {len(result.data)} active Data jobs without ranking_score:\n")

for job in result.data:
    print(f"Job: {job['title'][:60]}")
    print(f"   ID: {job['id']}")
    print(f"   Active: {job['is_active']}")
    print(f"   Classification: {job['title_classification']}")
    print(f"   Ranking Score: {job['ranking_score']}")
    print(f"   Base Score: {job['base_score']}")
    print(f"   Ranking Position: {job['ranking_position']}")
    print(f"   Needs Ranking: {job['needs_ranking']}")
    print(f"   Last Updated: {job['ranking_updated_at']}")
    print()

# Check if these jobs are in job_ranking_view
print("\n🔍 Checking if these jobs are in job_ranking_view...\n")

if result.data:
    job_ids = [job['id'] for job in result.data[:5]]
    
    for job_id in job_ids:
        view_result = db.client.table("job_ranking_view")\
            .select("job_posting_id, title, is_active, title_classification")\
            .eq("job_posting_id", job_id)\
            .execute()
        
        if view_result.data:
            print(f"✅ Job {job_id[:8]}... IS in job_ranking_view")
        else:
            print(f"❌ Job {job_id[:8]}... NOT in job_ranking_view")
            
            # Check why it's not in the view
            job_detail = db.client.table("job_postings")\
                .select("id, title, is_active, title_classification, company_id")\
                .eq("id", job_id)\
                .single()\
                .execute()
            
            # Check if it has llm_enrichment
            enrichment = db.client.table("llm_enrichment")\
                .select("job_posting_id")\
                .eq("job_posting_id", job_id)\
                .execute()
            
            print(f"   Job details: active={job_detail.data['is_active']}, classification={job_detail.data['title_classification']}")
            print(f"   Has enrichment: {len(enrichment.data) > 0}")
            print()

# Count total jobs without scores
total_count = db.client.table("job_postings")\
    .select("id", count="exact")\
    .is_("ranking_score", "null")\
    .eq("is_active", True)\
    .eq("title_classification", "Data")\
    .execute()

print(f"\n📊 Total active Data jobs without ranking_score: {total_count.count}")

# Count total active Data jobs
total_active = db.client.table("job_postings")\
    .select("id", count="exact")\
    .eq("is_active", True)\
    .eq("title_classification", "Data")\
    .execute()

print(f"📊 Total active Data jobs: {total_active.count}")
print(f"📊 Percentage without scores: {total_count.count / total_active.count * 100:.1f}%")
