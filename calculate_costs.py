#!/usr/bin/env python3
"""Calculate Bright Data costs per job."""

import asyncio
from database import db
from clients import get_client

# Bright Data pricing (from screenshot)
PRICING = {
    "pay_as_you_go": 0.60,  # $/GB
    "starter": 0.51,        # $/GB (min $499/mo)
    "advanced": 0.45,       # $/GB (min $999/mo)
    "advanced_plus": 0.42   # $/GB (min $1,999/mo)
}

async def calculate_costs():
    """Calculate cost per job based on recent scrapes."""
    
    print("💰 Bright Data Cost Analysis")
    print("=" * 80)
    
    # Get recent completed scrapes
    runs = db.get_scrape_runs(status="completed", limit=10)
    
    if not runs:
        print("No completed scrapes found")
        return
    
    client = get_client()
    
    total_jobs = 0
    total_data_mb = 0
    
    print("\n📊 Recent Scrapes:")
    print("-" * 80)
    
    for run in runs[:5]:  # Analyze last 5 scrapes
        query = run['search_query']
        location = run['location_query']
        jobs_found = run.get('jobs_found', 0)
        
        metadata = run.get('metadata', {})
        snapshot_id = metadata.get('snapshot_id')
        
        if not snapshot_id or jobs_found == 0:
            continue
        
        try:
            # Download to measure data size
            jobs = await client.download_results(snapshot_id)
            
            # Estimate data size (rough calculation)
            # Each job is approximately 2-5 KB of JSON data
            import json
            import sys
            
            # Calculate actual size
            jobs_json = json.dumps(jobs)
            data_size_bytes = sys.getsizeof(jobs_json)
            data_size_mb = data_size_bytes / (1024 * 1024)
            
            total_jobs += len(jobs)
            total_data_mb += data_size_mb
            
            print(f"\n{query} in {location}")
            print(f"  Jobs: {len(jobs)}")
            print(f"  Data size: {data_size_mb:.2f} MB")
            print(f"  Avg per job: {data_size_mb/len(jobs)*1024:.2f} KB")
            
        except Exception as e:
            print(f"  Error: {e}")
            continue
    
    await client.close()
    
    if total_jobs == 0:
        print("\nNo data to analyze")
        return
    
    # Calculate averages
    avg_mb_per_job = total_data_mb / total_jobs
    avg_gb_per_job = avg_mb_per_job / 1024
    
    print("\n" + "=" * 80)
    print("📈 Summary Statistics")
    print("-" * 80)
    print(f"Total jobs analyzed: {total_jobs}")
    print(f"Total data: {total_data_mb:.2f} MB ({total_data_mb/1024:.3f} GB)")
    print(f"Average per job: {avg_mb_per_job:.3f} MB ({avg_gb_per_job:.6f} GB)")
    
    print("\n" + "=" * 80)
    print("💵 Cost per Job (by plan)")
    print("-" * 80)
    
    for plan_name, price_per_gb in PRICING.items():
        cost_per_job = avg_gb_per_job * price_per_gb
        cost_per_100_jobs = cost_per_job * 100
        cost_per_1000_jobs = cost_per_job * 1000
        
        plan_display = plan_name.replace("_", " ").title()
        print(f"\n{plan_display} (${price_per_gb}/GB):")
        print(f"  Per job: ${cost_per_job:.4f}")
        print(f"  Per 100 jobs: ${cost_per_100_jobs:.2f}")
        print(f"  Per 1,000 jobs: ${cost_per_1000_jobs:.2f}")
    
    print("\n" + "=" * 80)
    print("🎯 Recommendations")
    print("-" * 80)
    
    # Calculate which plan is best
    monthly_jobs_estimate = 1000  # Adjust based on your needs
    
    for monthly_jobs in [100, 500, 1000, 5000, 10000]:
        print(f"\nIf you scrape {monthly_jobs:,} jobs/month:")
        
        best_plan = None
        best_cost = float('inf')
        
        for plan_name, price_per_gb in PRICING.items():
            cost = monthly_jobs * avg_gb_per_job * price_per_gb
            
            # Add minimum monthly fee for paid plans
            if plan_name == "starter":
                cost = max(cost, 499)
            elif plan_name == "advanced":
                cost = max(cost, 999)
            elif plan_name == "advanced_plus":
                cost = max(cost, 1999)
            
            plan_display = plan_name.replace("_", " ").title()
            print(f"  {plan_display:20s}: ${cost:8.2f}/month")
            
            if cost < best_cost:
                best_cost = cost
                best_plan = plan_display
        
        print(f"  → Best: {best_plan}")

if __name__ == "__main__":
    asyncio.run(calculate_costs())
