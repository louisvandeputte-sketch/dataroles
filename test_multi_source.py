#!/usr/bin/env python3
"""Test multi-source implementation."""

from database.client import db

print("Testing Multi-Source Implementation")
print("=" * 80)

# 1. Check jobs with multiple sources
print("\n1. Finding multi-source jobs...")
all_sources = db.client.table("job_sources")\
    .select("job_posting_id")\
    .execute()

from collections import Counter
job_counts = Counter([s['job_posting_id'] for s in all_sources.data])
multi_source_jobs = {k: v for k, v in job_counts.items() if v > 1}

print(f"   Found {len(multi_source_jobs)} jobs with multiple sources")

if multi_source_jobs:
    # Show examples
    print(f"\n2. Examples of multi-source jobs:")
    for job_id, source_count in list(multi_source_jobs.items())[:5]:
        # Get job details
        job = db.client.table("job_postings")\
            .select("title, companies(name)")\
            .eq("id", job_id)\
            .single()\
            .execute()
        
        # Get sources
        sources = db.client.table("job_sources")\
            .select("source, source_job_id")\
            .eq("job_posting_id", job_id)\
            .execute()
        
        company = job.data.get('companies', {}).get('name', 'N/A')
        source_list = [f"{s['source']} ({s['source_job_id'][:10]}...)" for s in sources.data]
        
        print(f"\n   {job.data['title']}")
        print(f"   Company: {company}")
        print(f"   Sources: {', '.join(source_list)}")

# 3. Test API response
print(f"\n3. Testing API response...")
import httpx
import asyncio

async def test_api():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/api/jobs/?limit=5")
        data = response.json()
        
        if data.get('jobs'):
            job = data['jobs'][0]
            print(f"   Sample job: {job.get('title')}")
            print(f"   job_sources field: {job.get('job_sources')}")
            
            if job.get('job_sources'):
                print(f"   ✅ job_sources is populated!")
                for source in job['job_sources']:
                    print(f"      - {source['source']}")
            else:
                print(f"   ⚠️  job_sources is empty or missing")

try:
    asyncio.run(test_api())
except Exception as e:
    print(f"   ⚠️  Could not test API: {e}")

# 4. Check dedup_key
print(f"\n4. Checking dedup_key...")
sample = db.client.table("job_postings")\
    .select("title, dedup_key, job_sources(source)")\
    .not_.is_("dedup_key", "null")\
    .limit(3)\
    .execute()

for job in sample.data:
    sources = [s['source'] for s in job.get('job_sources', [])]
    print(f"   {job['title'][:50]:50}")
    print(f"      dedup_key: {job['dedup_key'][:60]}")
    print(f"      sources: {sources}")

print("\n" + "=" * 80)
print("✅ Multi-source implementation test complete!")
print("\nNext: Test by scraping same job from both LinkedIn and Indeed")
