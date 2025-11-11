#!/usr/bin/env python3
"""Check API response for job_sources."""

import httpx
import asyncio

async def test():
    async with httpx.AsyncClient() as client:
        # Get jobs
        response = await client.get("http://localhost:8000/api/jobs/?limit=10")
        data = response.json()
        
        print("API Response Check")
        print("=" * 80)
        
        for i, job in enumerate(data['jobs'][:10], 1):
            title = job['title'][:40]
            sources = job.get('job_sources', [])
            source_names = [s['source'] for s in sources] if sources else ['NONE']
            
            print(f"\n{i}. {title}")
            print(f"   job_sources: {source_names}")
            print(f"   old source field: {job.get('source')}")

asyncio.run(test())
