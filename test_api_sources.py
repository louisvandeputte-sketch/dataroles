#!/usr/bin/env python3
"""Test API returns job_sources correctly."""

import httpx
import asyncio
import json

async def test():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/api/jobs/?limit=5")
        data = response.json()
        
        print("API /api/jobs/ Response Test")
        print("=" * 80)
        
        for i, job in enumerate(data['jobs'][:5], 1):
            print(f"\n{i}. {job['title'][:50]}")
            print(f"   source (old): {job.get('source')}")
            print(f"   job_sources (new): {job.get('job_sources')}")
            
            if not job.get('job_sources'):
                print(f"   ⚠️  job_sources is missing or empty!")
            elif not job.get('source'):
                print(f"   ⚠️  old source field is missing!")
            else:
                print(f"   ✅ Both fields present")

asyncio.run(test())
