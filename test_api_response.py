#!/usr/bin/env python3
"""Test API response structure."""

import asyncio
import httpx

async def test_api():
    print("Testing /api/jobs/ response")
    print("=" * 80)
    
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/api/jobs/?limit=3")
        data = response.json()
        
        print(f"\nStatus: {response.status_code}")
        print(f"Total jobs in response: {len(data.get('jobs', []))}")
        
        if data.get('jobs'):
            print("\nFirst job structure:")
            job = data['jobs'][0]
            print(f"  Title: {job.get('title')}")
            print(f"  Title Classification: {job.get('title_classification')}")
            print(f"  Job Types: {job.get('job_types')}")
            print(f"  AI Enriched: {job.get('ai_enriched')}")
            
            print("\nAll keys in first job:")
            for key in sorted(job.keys()):
                value = job[key]
                if isinstance(value, (dict, list)):
                    print(f"  {key}: {type(value).__name__}")
                else:
                    print(f"  {key}: {value}")

asyncio.run(test_api())
